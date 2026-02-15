# Next Steps to Run Your Incident & Ops Langchain Agent

You're almost ready to run your new Langchain Agent! Follow these steps to complete the setup and start interacting with it.

---



---

## 2. Install Project Dependencies

Make sure you are in the `incident_ops_agent` directory in your terminal. If not, navigate there:

```bash
cd incident_ops_agent
```

Then, install the required Python packages:

```bash
python3 -m pip install -r requirements.txt
```

---

## 3. Run the Agent

Once the `.env` file is updated and dependencies are installed, you can start the agent:

```bash
python3 main.py
```

The agent will start in interactive mode. You can type your queries, and it will respond using its tools and guardrails. Type `exit` to quit the agent.

---

## Example Interactions

Refer to the `README.md` file in the project directory for detailed examples of how to interact with the RAG, Calculator, and Mock Ticket API tools, as well as how the guardrails function.

---

## What's Next?

After successfully running the agent, consider exploring the "Extending the Project" section in the `README.md` for ideas on how to enhance this project further!
