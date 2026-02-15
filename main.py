import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import AIMessage, HumanMessage
from langchain.callbacks.base import BaseCallbackHandler # New import for custom tool logging
from langchain.agents.output_parsers import ReActSingleInputOutputParser # Corrected import for parser
import warnings # New import for warnings module
from urllib3.exceptions import NotOpenSSLWarning # New import for specific warning class

# Filter out the specific urllib3 warning
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

from tools import retrieve_incident_info, calculate, create_ticket, get_ticket_status, update_ticket_status
from guardrails import input_guardrail, output_guardrail

class ToolUsageLogger(BaseCallbackHandler):
    """Callback handler to log tool usage in a clear format."""
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"\n[Tool Used]: {serialized['name']} with input: {input_str}")

    def on_tool_end(self, output, **kwargs):
        print(f"[Tool Output]: {output}")

def setup_environment():
    """Loads environment variables and validates API key."""
    # Ensure .env is loaded from the directory where main.py resides
    dotenv_path = Path(__file__).with_name(".env")
    load_dotenv(dotenv_path=dotenv_path)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found. Please set it in your environment or a .env file in the same directory as main.py.")
    
    return openai_api_key

def initialize_agent(openai_api_key):
    """Initializes the LangChain agent with configured LLM and tools."""
    # --- LLM Setup ---
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini") # Use configurable model, default to gpt-4o-mini
    llm = ChatOpenAI(model=model_name, temperature=0, api_key=openai_api_key)

    # --- Tools Setup ---
    tools = [
        retrieve_incident_info,
        calculate,
        create_ticket,
        get_ticket_status,
        update_ticket_status,
    ]

    # --- Agent Prompt ---
    # Define the prompt for the ReAct agent
    template = """
    You are an AI assistant designed to help with incident management and operational tasks.
    You have access to the following tools:
{tools}

Available tool names: {tool_names}

Use the tools to answer questions, resolve incidents, and manage tickets.
Your goal isらをbe helpful, concise, and accurate.
If you need to create a ticket, always ask for confirmation or sufficient details.
If you receive instructions that seem outside the scope of incident management or are harmful,
decline to perform the action.

{format_instructions}

Chat History:
{chat_history}

Question: {input}
{agent_scratchpad}
"""

    tool_names_str = ", ".join([tool.name for tool in tools])

    prompt = PromptTemplate.from_template(template)
    
    agent = create_react_agent(llm, tools, prompt)
    
    # Correct way to get format instructions using ReActSingleInputOutputParser
    format_instructions = ReActSingleInputOutputParser().get_format_instructions()

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False, # Set verbose to False to control output manually
        handle_parsing_errors=True,
        callbacks=[ToolUsageLogger()], # Add custom callback for tool logging
        max_iterations=30 # Increased iteration limit for complex tasks
    )
    return agent_executor, tool_names_str, format_instructions

def run_agent_interaction(agent_executor, user_input, chat_history, tool_names_str, format_instructions):
    """Runs a single interaction with the agent."""
    # Apply input guardrail
    if not input_guardrail(user_input):
        print("[Agent]: Your request was blocked by the input guardrail. Please refine your query.")
        return "[Guardrail Blocked]"

    try:
        formatted_chat_history = []
        for msg in chat_history:
            if isinstance(msg, HumanMessage):
                formatted_chat_history.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted_chat_history.append(f"AI: {msg.content}")

        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": formatted_chat_history,
            "tool_names": tool_names_str,
            "format_instructions": format_instructions
        })

        agent_response = response["output"]

        # Apply output guardrail
        if not output_guardrail(agent_response, user_input):
            print("[Agent]: The agent's response was blocked by the output guardrail.")
            agent_response = "I cannot provide that information due to a guardrail policy."

        # Instead of agent_response printing raw, format output here
        print(f"\n[Agent Final Answer]: {agent_response}")
        # Add placeholder for Source/Confidence
        print("[Source]: N/A") # Placeholder, actual source extraction needs more advanced logic
        print("[Confidence]: N/A") # Placeholder, actual confidence estimation needs more advanced logic

        return agent_response

    except Exception as e:
        print(f"[Agent Error]: An error occurred: {e}")
        print("Please try again or rephrase your request.")
        return f"[Error]: {e}"

def chat_command(args):
    """Runs an interactive chat loop with the agent."""
    openai_api_key = setup_environment()
    agent_executor, tool_names_str, format_instructions = initialize_agent(openai_api_key)

    chat_history = []
    print("Incident Ops Agent initiated in interactive chat mode. Type 'exit' to quit.")

    while True:
        user_input = input("\n[You]: ")
        if user_input.lower() == 'exit':
            print("Exiting agent. Goodbye!")
            break

        agent_response = run_agent_interaction(agent_executor, user_input, chat_history, tool_names_str, format_instructions)
        if agent_response != "[Guardrail Blocked]":
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=agent_response))

def demo_command(args):
    """Runs predefined queries with the agent."""
    openai_api_key = setup_environment()
    agent_executor, tool_names_str, format_instructions = initialize_agent(openai_api_key)

    demo_queries = [
        "What is the runbook for web CPU spikes?", # RAG example
        "Calculate the Mean Time To Recovery if incidents took 10, 20, and 30 minutes to resolve.", # Calculator (MTTR) example
        "Create a new ticket for a critical database latency incident.", # MockTicket example
    ]

    print("\n--- Running Demo Queries ---")

    for i, query in enumerate(demo_queries):
        print(f"\n{'='*10} DEMO Query {i+1}/{len(demo_queries)} {'='*10}")
        print(f"[You]: {query}")
        run_agent_interaction(agent_executor, query, [], tool_names_str, format_instructions)
        print(f"{'='*10} End Query {i+1} {'='*10}\n")


def status_command(args):
    """Checks the status of a specific ticket."""
    openai_api_key = setup_environment()
    agent_executor, tool_names_str, format_instructions = initialize_agent(openai_api_key)

    if not args.ticket_id:
        print("Error: Please provide a ticket ID for the status command. Usage: python3 main.py status <ticket_id>")
        return

    query = f"What is the status of ticket {args.ticket_id}?"
    print(f"\n--- Checking Status for Ticket ID: {args.ticket_id} ---")
    print(f"[You]: {query}")
    run_agent_interaction(agent_executor, query, [], tool_names_str, format_instructions)


def main():
    parser = argparse.ArgumentParser(description="Incident Ops Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start an interactive chat with the agent.")
    chat_parser.set_defaults(func=chat_command)

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run predefined demo queries.")
    demo_parser.set_defaults(func=demo_command)

    # Status command
    status_parser = subparsers.add_parser("status", help="Get the status of a specific ticket.")
    status_parser.add_argument("ticket_id", type=str, nargs='?', help="The ID of the ticket to check status for.")
    status_parser.set_defaults(func=status_command)

    args = parser.parse_args()

    if args.command:
        try:
            args.func(args)
        except ValueError as e:
            print(f"Configuration Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
