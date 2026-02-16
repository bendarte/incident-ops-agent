# Incident/Ops CLI Agent (LangChain ReAct + Guardrails)

Detta repo demonstrerar en produktionsnära AI-agent för Incident/Ops med två tydliga kontrollvägar:

- Deterministisk routing för enkla, säkra operationer (`calculate`, `status INC-x`)
- LLM-baserad ReAct-agent för resonemang + verktygsanvändning

Målet är en stabil och förklarbar demo, inte maximal komplexitet.

## Arkitektur i korthet

- `main.py`: CLI, routing, policy enforcement och agent-exekvering.
- `tools.py`: verktyg för RAG, kalkyl och ticket-operationer.
- `ticket_adapter.py`: `TicketAdapter`-kontrakt + `MockTicketAdapter` (filbaserad backend).
- `guardrails.py`: input/output-skydd för policyblockering.
- `observability.py`: strukturerade JSON-events (audit/telemetry).

## Kontrollflöde

1. Input guardrail körs först.
2. Deterministisk route försöks först (om frågan matchar enkla mönster).
3. Annars går frågan till ReAct-agenten med verktyg.
4. Tool policy enforce: allowlist, exfiltration-check, explicit mutation-intent, `confirm=True` för muterande verktyg.
5. Output guardrail körs innan svar returneras.

## TicketAdapter-abstraktion

Ticketdelen är separerad från agentlogik:

- `TicketAdapter` definierar kontraktet (`create/get/update/reset`).
- `MockTicketAdapter` använder `tickets.json` för demo.
- Agenten använder verktygsfunktioner, inte backend-detaljer.

Det gör det enkelt att byta till Jira/ServiceNow senare utan att röra prompt/routing-flödet.

## Kom igång

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Skapa `.env` i projektroten:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
```

## Körning

Interaktiv chat:

```bash
python main.py chat
```

Deterministisk statusväg:

```bash
python main.py status INC-1
```

Repeterbar demo (rekommenderad inför intervju):

```bash
python main.py demo --reset-tickets
```

## Test

```bash
.venv/bin/pytest -q
```

## Observability

Agenten skriver JSON-events till stdout, t.ex.:

- `route_selected`
- `tool_start` / `tool_end`
- `guardrail_blocked`
- `policy_blocked`
- `agent_error`

Sätt `OPS_LOG_FILE` om du även vill spara events till fil.

## Intervjupitch (kort)

“Jag har separerat deterministiska operationer från LLM-resonemang för att minska risk och öka förutsägbarhet.  
Muterande actions kräver explicit intent + `confirm=True`.  
Ticket-backend ligger bakom en adapter, så mocken är stabil för demo men kan bytas mot riktig ITSM-integration utan att påverka agentens kärnflöde.”

## Medvetna tradeoffs

- Mock backend i stället för real integration: snabb och stabil demo.
- Enkla guardrails/pattern checks i stället för tung policy-engine.
- Lätt observability via stdout JSON i stället för full telemetry-stack.
