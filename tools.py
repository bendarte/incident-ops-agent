import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.tools import tool
import operator
import re
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# --- RAG Tool Setup ---

class RetrieveIncidentInfoInput(BaseModel):
    query: str = Field(description="The natural language query or description of the incident/problem to retrieve information for.")

class RagTool:
    _instance = None
    _vectorstore = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RagTool, cls).__new__(cls)
            cls._instance._initialize_vectorstore()
        return cls._instance

    def _initialize_vectorstore(self):
        if self.__class__._vectorstore is not None:
            return

        print("Initializing RAG vector store...")
        script_dir = os.path.dirname(__file__)
        corpus_dir = os.path.join(script_dir, "corpus")

        documents = []
        for filename in os.listdir(corpus_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(corpus_dir, filename)
                loader = TextLoader(file_path)
                documents.extend(loader.load())

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)

        # Ensure OPENAI_API_KEY is set
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not found. Please set it in your environment or a .env file.")

        embeddings = OpenAIEmbeddings()
        self.__class__._vectorstore = FAISS.from_documents(splits, embeddings)
        print("RAG vector store initialized.")

rag_tool_instance = RagTool()

@tool(args_schema=RetrieveIncidentInfoInput)
def retrieve_incident_info(query: str) -> str:
    """
    Retrieves relevant information from incident reports, runbooks, and operational
    documentation based on a natural language query.
    Useful for understanding past incidents, finding runbook steps for specific issues,
    or getting context on operational procedures.

    Input should be a clear question or description of the incident/problem.
    For example: "What caused the database latency on Feb 15?",
    "How to handle a web server CPU spike?",
    "What are the next steps after a database incident?"
    """
    if rag_tool_instance._vectorstore is None:
        raise RuntimeError("RAG vector store not initialized.")
    docs = rag_tool_instance._vectorstore.similarity_search(query)
    return "\n\n".join([doc.page_content for doc in docs])


# --- Calculator Tool ---
@tool
def calculate(expression: str) -> str:
    """
    Evaluates a mathematical expression.
    Use this for any arithmetic calculations.
    Input should be a valid mathematical expression string (e.g., "2 + 2", "(5 * 3) / 2").
    Supported operations: +, -, *, /, **, %.
    """
    try:
        # Basic sanitization to prevent arbitrary code execution
        if not re.match(r"^[0-9+\-*/().\s%]+$", expression):
            return "Error: Invalid characters in expression."
        # Use a safe evaluation method, 'operator' module is safer than eval()
        # For simplicity, we'll use eval() with extreme caution, but in production,
        # a more robust parsing and evaluation library (like ast.literal_eval or numexpr)
        # would be preferred.
        # This is a common pattern in Langchain examples for calculator tools,
        # but be aware of the security implications of eval().
        return str(eval(expression))
    except Exception as e:
        return f"Error evaluating expression: {e}"


# --- Mock Ticket API Tool ---
class MockTicketAPI:
    def __init__(self):
        self.tickets = {}
        self.ticket_id_counter = 1

    @tool
    def create_ticket(self, title: str, description: str, severity: str = "Medium") -> str:
        """
        Creates a new incident ticket in the system.
        Requires a 'title' and 'description' for the ticket.
        Optional 'severity' can be 'Low', 'Medium', 'High', 'Critical'. Defaults to 'Medium'.
        Returns the ID of the newly created ticket.
        """
        new_ticket_id = f"INC-{self.ticket_id_counter}"
        self.tickets[new_ticket_id] = {
            "title": title,
            "description": description,
            "severity": severity,
            "status": "Open"
        }
        self.ticket_id_counter += 1
        return f"Ticket '{new_ticket_id}' created successfully with title: '{title}' and severity: '{severity}'."

    @tool
    def get_ticket_status(self, ticket_id: str) -> str:
        """
        Retrieves the current status and details of an existing incident ticket.
        Requires the 'ticket_id' (e.g., "INC-1").
        Returns the ticket details or an error if not found.
        """
        ticket = self.tickets.get(ticket_id)
        if ticket:
            return (f"Ticket ID: {ticket_id}\n"
                    f"Title: {ticket['title']}\n"
                    f"Description: {ticket['description']}\n"
                    f"Severity: {ticket['severity']}\n"
                    f"Status: {ticket['status']}")
        return f"Error: Ticket '{ticket_id}' not found."

    @tool
    def update_ticket_status(self, ticket_id: str, new_status: str) -> str:
        """
        Updates the status of an existing incident ticket.
        Requires the 'ticket_id' (e.g., "INC-1") and the 'new_status'.
        Valid statuses are: 'Open', 'In Progress', 'Resolved', 'Closed', 'On Hold'.
        Returns a confirmation message or an error if not found/invalid status.
        """
        if new_status not in ["Open", "In Progress", "Resolved", "Closed", "On Hold"]:
            return f"Error: Invalid status '{new_status}'. Valid statuses are 'Open', 'In Progress', 'Resolved', 'Closed', 'On Hold'."

        ticket = self.tickets.get(ticket_id)
        if ticket:
            ticket['status'] = new_status
            return f"Ticket '{ticket_id}' status updated to '{new_status}'."
        return f"Error: Ticket '{ticket_id}' not found."

# Initialize Mock Ticket API
mock_ticket_api_instance = MockTicketAPI()
create_ticket = mock_ticket_api_instance.create_ticket
get_ticket_status = mock_ticket_api_instance.get_ticket_status
update_ticket_status = mock_ticket_api_instance.update_ticket_status
