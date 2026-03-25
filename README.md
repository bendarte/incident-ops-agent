# Incident/Ops CLI Agent (LangChain ReAct + Guardrails)

Portfolioprojekt för Incident/Ops byggt för att visa kontrollerad agentdesign, inte bara "en chatbot med tools".

Agenten använder två kontrollvägar:

- Deterministisk routing för enkla och säkra operationer (`calculate`, `status INC-x`, explicit ticket update med `confirm=True`)
- LLM-baserad ReAct-agent för resonemang och verktygsanvändning

Målet är en stabil, förklarbar och demo-vänlig agent.

## Kort pitch

`incident-ops-agent` är en Python-baserad CLI-agent för incidentarbete som kombinerar deterministisk routing för säkra high-confidence-actions med en LangChain ReAct-agent för resonemang och verktygsanvändning.

Det viktiga här är inte bara att modellen kan svara, utan att agenten är styrbar:

- säkra operationer går inte via LLM i onödan
- muterande actions kräver tydlig intent och `confirm=True`
- retrieval-svar visar källor
- policy och guardrails stoppar prompt-/secret-försök tidigt

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

## Screenshots

### RAG med källor

![RAG med källor](docs/screenshots/01-rag-with-sources.png)

### Guardrail-blockering

![Guardrail-blockering](docs/screenshots/02-guardrail-blocking.png)

### Ticket creation

![Ticket creation](docs/screenshots/03-ticket-creation.png)

### Ticket update

![Ticket update](docs/screenshots/04-ticket-update.png)

### Quality checks

![Quality checks](docs/screenshots/05-quality-checks.png)

Rekommenderad demoordning i intervju:

1. RAG med källor
2. Deterministisk beräkning
3. Guardrail-blockering
4. Skapa ärende med `confirm=True`
5. Uppdatera ärende med deterministisk route

## Varför det här är relevant för AI-roller

Det här projektet visar praktiska delar som ofta efterfrågas i AI Engineer/Applied AI-roller:

- Hybridarkitektur: tydlig separation mellan deterministisk logik och LLM-resonemang.
- Säkerhet och styrning: input/output-guardrails, tool allowlist, exfiltration-check, `confirm=True` för muterande actions.
- Tooling och agentdesign: ReAct-agent med verktyg för RAG, beräkning och ticket-flöden.
- Systemdesign: `TicketAdapter` gör att mock-backend kan bytas mot Jira/ServiceNow utan att ändra agentens kärnflöde.
- Driftbarhet: strukturerad observability (`route_selected`, `tool_start`, `guardrail_blocked`, etc.) för felsökning och audit.

Kort sagt: den demonstrerar inte bara “att modellen svarar”, utan hur man bygger en kontrollerad AI-agent som är intervju- och demo-vänlig.

## Case study

Problem:
Vanliga tool-using demos visar ofta att modellen kan anropa verktyg, men inte hur man begränsar beteendet när ett svar kan påverka drift, ärenden eller känslig information.

Lösning:
Jag byggde därför agenten runt en hybrid kontrollmodell där enkla och säkra flöden routas deterministiskt, medan mer öppna frågor går via en LLM-agent med separat policy enforcement.

Resultat:
- enklare operationer blir snabbare och mer förutsägbara
- muterande actions är svårare att trigga av misstag
- RAG-svar blir lättare att granska eftersom källor visas
- systemet går att demo:a och förklara utan att låtsas vara mer produktionsredo än det är

## Designval

- Deterministisk routing före LLM:
  Billigare, snabbare och lättare att försvara för beräkning, ticket-status och tydliga uppdateringar.
- Adapter för ticket-backend:
  Mockad lagring nu, men samma gränsyta kan senare peka mot Jira eller ServiceNow.
- Lätta guardrails i stället för tung policy-motor:
  Medvetet val för att hålla repot läsbart och intervjuvänligt.
- Strukturerad observability i stdout:
  Tillräckligt för demo, felsökning och audit utan att bygga en hel telemetry-stack.

## Arkitektur

- `main.py`: CLI, routing, policy enforcement och agent-exekvering.
- `policy.py`: tool policy, intent-checkar och confirm-regler.
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

Exempel på prompts:

```text
Vad säger runbooken om CPU-spikar på webbservrar?
Beräkna (18 + 24 + 36) / 3
Skapa ett nytt ärende. Titel: "DB latency", Beskrivning: "Slow queries", Severity: "High". confirm=True.
Uppdatera ärende INC-1. Ny status: "Resolved". confirm=True.
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

## Kvalitet

Installera utvecklarverktygen om du vill köra samma kontroller lokalt som i CI:

```bash
python -m pip install -r requirements-dev.txt
ruff check .
.venv/bin/pytest -q
```

GitHub Actions kör både `ruff check .` och `pytest -q` på pushes till `main` och på pull requests.

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

## Så kan projektet beskrivas i intervju

- Jag byggde det som en kontrollerad Incident/Ops-agent, inte som en generell chatbot, så att jag kunde visa routing, guardrails, tool policy och observability i samma repo.
- Jag valde deterministisk routing för säkra operationer och LLM-resonemang bara där det faktiskt behövs.
- Jag höll backend mockad medvetet, för att fokusera på styrning, testbarhet och arkitektur i stället för integrationsteater.

## CV-/LinkedIn-bullets

- Built a Python CLI Incident/Ops AI agent with deterministic routing, LangChain ReAct tooling, guardrails, and policy enforcement.
- Implemented local RAG with source attribution, structured JSON observability, and adapter-based ticket operations.
- Added tests, linting, Docker, and CI to keep the project demoable, reviewable, and technically defensible.
