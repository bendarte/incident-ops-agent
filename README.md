# Incident/Ops CLI Agent (LangChain ReAct + Guardrails)

Portfolioprojekt för Incident/Ops byggt för att visa kontrollerad agentdesign, inte bara "en chatbot med tools".

Agenten använder två kontrollvägar:

- Deterministisk routing för enkla och säkra operationer (`calculate`, `status INC-x`, explicit ticket update med `confirm=True`)
- LLM-baserad ReAct-agent för resonemang och verktygsanvändning

Målet är en stabil, förklarbar och demo-vänlig agent.

## Vad projektet visar

- hybrid kontrollmodell: deterministisk routing för låg-risk/high-confidence actions, LLM för resonemang
- guardrails på input, output och tool policy
- adapter-baserad ticket backend som kan bytas mot Jira/ServiceNow senare
- lokal RAG över incident/runbook-corpus med källor i slutsvaret
- strukturerad observability via JSON-events
- testbar design med `pytest`

## Demo och material

- Portfolio-sida som refererar projektet: https://osmanen.vercel.app
- Repeterbar CLI-demo: `python3 main.py demo --reset-tickets`
- Interaktiv chat: `python3 main.py chat`
- Lokala skärmfilmer: `demos/osman_demo_2.mov`, `demos/Osman_demo_1.mov`

## Varför det här är relevant för AI-roller

Det här projektet visar praktiska delar som ofta efterfrågas i AI Engineer/Applied AI-roller:

- Hybridarkitektur: tydlig separation mellan deterministisk logik och LLM-resonemang.
- Säkerhet och styrning: input/output-guardrails, tool allowlist, exfiltration-check, `confirm=True` för muterande actions.
- Tooling och agentdesign: ReAct-agent med verktyg för RAG, beräkning och ticket-flöden.
- Systemdesign: `TicketAdapter` gör att mock-backend kan bytas mot Jira/ServiceNow utan att ändra agentens kärnflöde.
- Driftbarhet: strukturerad observability (`route_selected`, `tool_start`, `guardrail_blocked`, etc.) för felsökning och audit.

Kort sagt: den demonstrerar inte bara “att modellen svarar”, utan hur man bygger en kontrollerad AI-agent som är intervju- och demo-vänlig.

## Arkitektur

- `main.py`: CLI, routing, policy enforcement och agent-exekvering.
- `tools.py`: verktyg för RAG, kalkyl och ticket-operationer.
- `ticket_adapter.py`: `TicketAdapter` + `MockTicketAdapter` (`tickets.json`).
- `guardrails.py`: input/output-skydd.
- `observability.py`: strukturerade JSON-events.

Förenklad kontrollmodell:

```text
User input
  -> input_guardrail
  -> deterministic route?
       -> yes: tool invoke -> output_guardrail -> final answer
       -> no: ReAct agent -> tool policy via callback -> output_guardrail -> final answer
```

## Kontrollflöde

1. Input guardrail.
2. Deterministisk route (om frågan matchar säkra mönster).
3. Annars ReAct-agent med verktyg.
4. Tool policy enforcement (allowlist, exfiltration-check, intent-check, `confirm=True` för mutationer).
5. Output guardrail innan svar returneras.
6. Om RAG-verktyget returnerar källor visas de i slutsvaret.

## Kom igång

Krav: Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp sample.env .env
```

Uppdatera sedan `.env` i projektroten:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
OPS_MAX_ITERATIONS=12
OPS_MAX_EXECUTION_SECONDS=20
```

## Körning

```bash
python3 main.py chat
python3 main.py status INC-1
python3 main.py demo --reset-tickets
```

## Docker

Bygg en enkel lokal image:

```bash
docker build -t incident-ops-agent .
```

Kör sedan valfritt CLI-kommando, till exempel demo:

```bash
docker run --rm \
  --env-file .env \
  incident-ops-agent python main.py demo --reset-tickets
```

## Test

```bash
.venv/bin/pytest -q
```

GitHub Actions kör samma `pytest -q` på pushes till `main` och på pull requests.

## Begränsningar

- mockad ticket-backend, inte riktig ITSM-integration
- ingen live webbtjänst; detta är i första hand ett CLI-projekt
- guardrails är avsiktligt lätta och läsbara, inte en full policy-motor
- lokal FAISS-cache använder pickle och ska bara laddas från betrodd lokal källa

## Observability

Agenten loggar JSON-events till stdout, t.ex.:

- `route_selected`
- `tool_start`, `tool_end`
- `guardrail_blocked`
- `policy_blocked`
- `agent_error`

Sätt `OPS_LOG_FILE` för att även skriva till fil.

## Tradeoffs

- Mock-backend i stället för live ITSM-integration: snabbare och stabilare demo.
- Lätta guardrails i stället för tung policy-motor: enklare att förstå och utöka.
- JSON-logs i stdout i stället för full telemetry-stack: tillräckligt för demo/intervju.
