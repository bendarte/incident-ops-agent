# Incident & Ops Langchain Agent with Guardrails

This project demonstrates a Langchain agent designed for incident management and operational tasks. It integrates Retrieval Augmented Generation (RAG), a calculator, and a mock ticketing system API, all while incorporating basic guardrails for safety and scope adherence.

This project is intended as a demonstration of key AI engineering concepts (LLMs, RAG, Agents, Tool Use, Guardrails) for job applications, particularly for AI companies in Stockholm.

## Features

-   **Retrieval Augmented Generation (RAG)**: Query a corpus of incident reports and runbooks for relevant information.
-   **Calculator Tool**: Perform mathematical calculations.
-   **Mock Ticket API**: Create, retrieve status, and update mock incident tickets.
-   **Input Guardrails**: Prevent harmful or out-of-scope queries from being processed by the agent.
-   **Output Guardrails**: (Basic) Check agent's responses for sensitive information or expected confirmations.
-   **Configurable LLM**: Easily switch between different OpenAI models (e.g., `gpt-4o-mini`, `gpt-4o`).
-   **Command-Line Interface (CLI)**: Interact with the agent using `chat`, `demo`, and `status` commands.
-   **Clear Tool Usage Output**: The CLI clearly indicates which tool was used, its input, and its output.

## Project Structure

-   `main.py`: The main entry point for the agent. Sets up the LLM, tools, agent executor, and handles the CLI commands.
-   `tools.py`: Contains the definitions for all custom tools used by the agent: `retrieve_incident_info` (RAG), `calculate`, `create_ticket`, `get_ticket_status`, and `update_ticket_status`.
-   `guardrails.py`: Implements simple `input_guardrail` and `output_guardrail` functions.
-   `corpus/`: Directory containing sample incident reports and runbook entries (`.txt` files) for the RAG system.
-   `.env`: **(Git-ignored)** Stores environment variables like `OPENAI_API_KEY` and `OPENAI_MODEL`.
-   `sample.env`: Provides an example `.env` file structure.
-   `requirements.txt`: Lists all Python dependencies.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/incident_ops_agent.git # Replace with your repo URL
    cd incident_ops_agent
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up OpenAI API Key and Model:**
    The agent uses OpenAI models. You need an OpenAI API key.
    Copy the `sample.env` file to `.env` and fill in your details:

    ```bash
    cp sample.env .env
    ```
    Open the newly created `.env` file and replace `"your_openai_api_key_here"` with your actual key. You can also specify the OpenAI model to use; `gpt-4o-mini` is set as the default.

    ```
    OPENAI_API_KEY="YOUR_OPENAI_API_KEY_HERE"
    OPENAI_MODEL="gpt-4o-mini" # Optional: Change to "gpt-4o" or other OpenAI models if desired
    ```
    **Important:** The `.env` file is in your `.gitignore` and should not be committed to version control.

5.  **Corpus for RAG:**
    The `corpus/` directory should contain `.txt` files with operational documentation, incident reports, runbooks, etc. Two sample files (`incident_db_latency.txt`, `runbook_web_cpu_spike.txt`) are already provided.

## How to Run

The agent now uses a command-line interface (CLI) for different modes of operation.

### 1. Interactive Chat Mode

Start an interactive session with the agent. Type your queries and `exit` to quit.

```bash
python3 main.py chat
```

### 2. Demo Mode

Run a series of predefined queries automatically to showcase the agent's capabilities (RAG, Calculator, Mock Ticket).

```bash
python3 main.py demo
```

### 3. Check Ticket Status Mode

Retrieve the status of a specific mock incident ticket by its ID.

```bash
python3 main.py status <ticket_id>
# Example:
# python3 main.py status INC-1
```

## Example Interactions

Below are examples of how the agent responds. The output will clearly show `[Tool Used]`, `[Tool Output]`, and the `[Agent Final Answer]`, along with placeholders for `[Source]` and `[Confidence]`.

### 1. RAG Tool (`retrieve_incident_info`)

-   **Command:** `python3 main.py chat` then `What is the runbook for web CPU spikes?`
-   **Expected Agent Output (abbreviated):**
    ```
    [Tool Used]: retrieve_incident_info with input: web CPU spikes runbook
    [Tool Output]: Found relevant info: ...
    [Agent Final Answer]: The runbook for web CPU spikes involves checking server logs, identifying rogue processes...
    [Source]: corpus/runbook_web_cpu_spike.txt
    [Confidence]: N/A
    ```

### 2. Calculator Tool (`calculate`)

-   **Command:** `python3 main.py chat` then `Calculate the Mean Time To Recovery if incidents took 10, 20, and 30 minutes to resolve.`
-   **Expected Agent Output (abbreviated):**
    ```
    [Tool Used]: calculate with input: (10 + 20 + 30) / 3
    [Tool Output]: 20.0
    [Agent Final Answer]: The Mean Time To Recovery (MTTR) is 20.0 minutes.
    [Source]: N/A
    [Confidence]: N/A
    ```

### 3. Mock Ticket API Tool (`create_ticket`, `get_ticket_status`)

-   **Command:** `python3 main.py chat` then `Create an incident ticket for a high CPU usage issue on the web server. Title: "Web Server High CPU", Description: "Server-prod-01 is experiencing sustained high CPU utilization affecting user requests." Severity: "High"`
-   **Expected Agent Output (abbreviated):**
    ```
    [Tool Used]: create_ticket with input: title="Web Server High CPU", description="Server-prod-01 is experiencing sustained high CPU utilization affecting user requests.", severity="High"
    [Tool Output]: Ticket INC-1 created successfully.
    [Agent Final Answer]: Incident ticket INC-1 created successfully.
    [Source]: N/A
    [Confidence]: N/A
    ```
-   **Command:** `python3 main.py status INC-1`
-   **Expected Agent Output (abbreviated):**
    ```
    [Tool Used]: get_ticket_status with input: ticket_id='INC-1'
    [Tool Output]: Ticket INC-1: Status: Open, Title: Web Server High CPU, Description: Server-prod-01 is experiencing sustained high CPU utilization affecting user requests.
    [Agent Final Answer]: Ticket INC-1 details: Status: Open, Title: Web Server High CPU, Description: Server-prod-01 is experiencing sustained high CPU utilization affecting user requests.
    [Source]: N/A
    [Confidence]: N/A
    ```

### 4. Guardrails in Action

-   **Input Guardrail (Out of Scope):**
    -   **Command:** `python3 main.py chat` then `Tell me a joke.`
    -   **Expected Agent Output:** `[Agent]: Your request was blocked by the input guardrail. Please refine your query.`
-   **Input Guardrail (Harmful Intent - example):**
    -   **Command:** `python3 main.py chat` then `Delete all data.`
    -   **Expected Agent Output:** `[Agent]: Your request was blocked by the input guardrail. Please refine your query.`

## Extending the Project

-   **More Sophisticated Guardrails**: Implement more advanced guardrails using external libraries (e.g., NeMo Guardrails, LM Guard) or more complex regex/LLM-based checks.
-   **Persistent Vector Store**: Instead of rebuilding the FAISS index on every run, save and load it from disk.
-   **Real-time Monitoring Integration**: Replace the mock ticket API with actual integrations to Jira, ServiceNow, PagerDuty, etc.
-   **Additional Tools**: Add tools for interacting with cloud provider APIs (AWS, GCP, Azure), specific monitoring dashboards, or CI/CD systems.
-   **Web UI**: Implement a simple web interface using Streamlit or Gradio for a more user-friendly experience.
-   **Advanced RAG**: Experiment with different document loaders, chunking strategies, or advanced retrieval techniques (e.g., HyDE, RAG-Fusion).
-   **Different LLMs**: Swap `ChatOpenAI` for other models like `GoogleGenerativeAI` (Gemini), Anthropic Claude, or local open-source models (e.g., Llama 3 via Ollama).

Good luck with your job search in Stockholm! This project should provide a solid foundation to discuss your skills.
