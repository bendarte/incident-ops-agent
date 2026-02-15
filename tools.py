# tools.py
from __future__ import annotations

import ast
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Tuple

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field

load_dotenv()

# -----------------------------
# RAG (with sources + cache)
# -----------------------------

class RetrieveIncidentInfoInput(BaseModel):
    query: str = Field(
        description="Natural language question about an incident/runbook. Example: 'What caused DB latency on Feb 15?'"
    )

@dataclass
class RagResult:
    text: str
    sources: List[str]

class RagTool:
    """
    Lazy-load FAISS index from disk if available.
    If not, build it from corpus/*.txt and persist it.
    """
    def __init__(self) -> None:
        self._vectorstore: FAISS | None = None

        self._root = Path(__file__).parent
        self._corpus_dir = self._root / "corpus"
        self._index_dir = self._root / ".faiss_index"  # cached artifacts (safe to gitignore)
        self._index_dir.mkdir(exist_ok=True)

    def _ensure_api_key(self) -> None:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not found. Please set it in your environment or a .env file.")

    def _load_or_build(self) -> FAISS:
        if self._vectorstore is not None:
            return self._vectorstore

        self._ensure_api_key()
        embeddings = OpenAIEmbeddings()

        # Try load
        faiss_path = str(self._index_dir)
        index_file = self._index_dir / "index.faiss"
        store_file = self._index_dir / "index.pkl"
        if index_file.exists() and store_file.exists():
            self._vectorstore = FAISS.load_local(
                faiss_path,
                embeddings,
                allow_dangerous_deserialization=True,  # FAISS uses pickle
            )
            return self._vectorstore

        # Build
        if not self._corpus_dir.exists():
            raise FileNotFoundError(f"Corpus directory not found: {self._corpus_dir}")

        documents = []
        for fp in sorted(self._corpus_dir.glob("*.txt")):
            loader = TextLoader(str(fp), encoding="utf-8")
            docs = loader.load()
            # Ensure source metadata is present
            for d in docs:
                d.metadata = d.metadata or {}
                d.metadata["source"] = f"corpus/{fp.name}"
            documents.extend(docs)

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = splitter.split_documents(documents)

        self._vectorstore = FAISS.from_documents(splits, embeddings)
        self._vectorstore.save_local(faiss_path)
        return self._vectorstore

    def search(self, query: str, k: int = 4) -> RagResult:
        vs = self._load_or_build()
        docs = vs.similarity_search(query, k=k)

        sources: List[str] = []
        chunks: List[str] = []
        for d in docs:
            src = (d.metadata or {}).get("source", "unknown_source")
            sources.append(src)
            chunks.append(d.page_content)

        # Unique sources, keep order
        uniq_sources = list(dict.fromkeys(sources))
        return RagResult(text="\n\n".join(chunks), sources=uniq_sources)

_rag = RagTool()

@tool(args_schema=RetrieveIncidentInfoInput)
def retrieve_incident_info(query: str) -> str:
    """
    Retrieve relevant information from corpus/ based on a natural language query.
    Returns a structured string that includes sources.
    """
    result = _rag.search(query)
    sources_str = ", ".join(result.sources) if result.sources else "unknown_source"
    return f"{result.text}\n\n[SOURCES]: {sources_str}"

# -----------------------------
# Safe Calculator (no eval)
# -----------------------------

_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
}
_ALLOWED_UNARYOPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}

def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return float(_ALLOWED_BINOPS[type(node.op)](left, right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        operand = _safe_eval(node.operand)
        return float(_ALLOWED_UNARYOPS[type(node.op)](operand))
    raise ValueError("Unsupported or unsafe expression.")

@tool
def calculate(expression: str) -> str:
    """
    Safely evaluates arithmetic expressions (no eval).
    Supported: +, -, *, /, **, %, parentheses, integers/floats.
    """
    try:
        parsed = ast.parse(expression, mode="eval")
        value = _safe_eval(parsed)
        # Pretty output: avoid trailing .0 for integers
        return str(int(value)) if value.is_integer() else str(value)
    except Exception as e:
        return f"Error evaluating expression: {e}"

# -----------------------------
# Mock Ticket API (with confirmation gate + optional persistence)
# -----------------------------

_TICKETS_PATH = Path(__file__).parent / "tickets.json"

class MockTicketAPI:
    def __init__(self) -> None:
        self.tickets: dict[str, dict[str, Any]] = {}
        self.ticket_id_counter = 1
        self._load()

    def _load(self) -> None:
        if _TICKETS_PATH.exists():
            try:
                data = json.loads(_TICKETS_PATH.read_text(encoding="utf-8"))
                self.tickets = data.get("tickets", {})
                self.ticket_id_counter = int(data.get("ticket_id_counter", 1))
            except Exception:
                # If corrupted, start fresh (demo project)
                self.tickets = {}
                self.ticket_id_counter = 1

    def _save(self) -> None:
        payload = {
            "ticket_id_counter": self.ticket_id_counter,
            "tickets": self.tickets,
        }
        _TICKETS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @tool
    def create_ticket(self, title: str, description: str, severity: str = "Medium", confirm: bool = False) -> str:
        """
        Creates a new incident ticket.
        NOTE: Requires confirm=True to actually create the ticket.
        """
        if not confirm:
            return (
                "Confirmation required. Re-run create_ticket with confirm=True after you verify:\n"
                f"- title='{title}'\n- severity='{severity}'\n"
                "This prevents accidental ticket creation."
            )

        new_ticket_id = f"INC-{self.ticket_id_counter}"
        self.tickets[new_ticket_id] = {
            "title": title,
            "description": description,
            "severity": severity,
            "status": "Open",
        }
        self.ticket_id_counter += 1
        self._save()
        return f"Ticket '{new_ticket_id}' created successfully with title: '{title}' and severity: '{severity}'."

    @tool
    def get_ticket_status(self, ticket_id: str) -> str:
        """
        Retrieves ticket status/details.
        """
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return f"Error: Ticket '{ticket_id}' not found."
        return (
            f"Ticket ID: {ticket_id}\n"
            f"Title: {ticket['title']}\n"
            f"Description: {ticket['description']}\n"
            f"Severity: {ticket['severity']}\n"
            f"Status: {ticket['status']}"
        )

    @tool
    def update_ticket_status(self, ticket_id: str, new_status: str, confirm: bool = False) -> str:
        """
        Updates ticket status.
        NOTE: Requires confirm=True to apply the update.
        """
        valid = ["Open", "In Progress", "Resolved", "Closed", "On Hold"]
        if new_status not in valid:
            return f"Error: Invalid status '{new_status}'. Valid statuses are: {', '.join(valid)}."

        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return f"Error: Ticket '{ticket_id}' not found."

        if not confirm:
            return (
                "Confirmation required. Re-run update_ticket_status with confirm=True after you verify:\n"
                f"- ticket_id='{ticket_id}'\n- new_status='{new_status}'"
            )

        ticket["status"] = new_status
        self._save()
        return f"Ticket '{ticket_id}' status updated to '{new_status}'."

mock_ticket_api_instance = MockTicketAPI()
create_ticket = mock_ticket_api_instance.create_ticket
get_ticket_status = mock_ticket_api_instance.get_ticket_status
update_ticket_status = mock_ticket_api_instance.update_ticket_status
