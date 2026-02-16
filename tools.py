# tools.py
from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field
from ticket_adapter import MockTicketAdapter

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
        try:
            embeddings = OpenAIEmbeddings()
        except Exception as e:
            raise RuntimeError(
                "Failed to initialize OpenAI embeddings. Verify OPENAI_API_KEY and model access."
            ) from e

        # Try load
        faiss_path = str(self._index_dir)
        index_file = self._index_dir / "index.faiss"
        store_file = self._index_dir / "index.pkl"
        if index_file.exists() and store_file.exists():
            try:
                self._vectorstore = FAISS.load_local(
                    faiss_path,
                    embeddings,
                    allow_dangerous_deserialization=True,  # FAISS uses pickle
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load FAISS index from '{self._index_dir}'. "
                    "Delete '.faiss_index/' and retry to rebuild."
                ) from e
            return self._vectorstore

        # Build
        if not self._corpus_dir.exists():
            raise FileNotFoundError(f"Corpus directory not found: {self._corpus_dir}")

        documents = []
        for fp in sorted(self._corpus_dir.glob("*.txt")):
            try:
                loader = TextLoader(str(fp), encoding="utf-8")
                docs = loader.load()
            except Exception as e:
                raise RuntimeError(f"Failed to load corpus file '{fp}'.") from e
            # Ensure source metadata is present
            for d in docs:
                d.metadata = d.metadata or {}
                d.metadata["source"] = f"corpus/{fp.name}"
            documents.extend(docs)

        if not documents:
            raise FileNotFoundError(
                f"No .txt files found in corpus directory: {self._corpus_dir}"
            )

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = splitter.split_documents(documents)

        try:
            self._vectorstore = FAISS.from_documents(splits, embeddings)
            self._vectorstore.save_local(faiss_path)
        except Exception as e:
            raise RuntimeError(
                f"Failed to build or persist FAISS index in '{self._index_dir}'."
            ) from e
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
# Ticket tools via adapter abstraction (mock backend by default)
# -----------------------------

_TICKETS_PATH = Path(__file__).parent / "tickets.json"
_ticket_adapter = MockTicketAdapter(storage_path=_TICKETS_PATH)

@tool
def create_ticket(title: str, description: str, severity: str = "Medium", confirm: bool = False) -> str:
    """
    Creates a new incident ticket.
    NOTE: Requires confirm=True to actually create the ticket.
    """
    return _ticket_adapter.create_ticket(title=title, description=description, severity=severity, confirm=confirm)


@tool
def get_ticket_status(ticket_id: str) -> str:
    """
    Retrieves ticket status/details.
    """
    return _ticket_adapter.get_ticket_status(ticket_id=ticket_id)


@tool
def update_ticket_status(ticket_id: str, new_status: str, confirm: bool = False) -> str:
    """
    Updates ticket status.
    NOTE: Requires confirm=True to apply the update.
    """
    return _ticket_adapter.update_ticket_status(ticket_id=ticket_id, new_status=new_status, confirm=confirm)


def reset_ticket_store() -> None:
    _ticket_adapter.reset_store()
