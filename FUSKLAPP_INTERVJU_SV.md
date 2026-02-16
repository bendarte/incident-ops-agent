# Fusklapp (Intervju)

## Varför denna lösning
- Delar upp kontroll i deterministisk väg + LLM-väg.
- Minskar risk för mutationer via policy + `confirm=True`.
- Visar production mindset: tester, observability, repeterbar demo.

## Demo på 60 sekunder
1. RAG-fråga (LLM-väg): visar resonemang + källstöd.
2. Beräkning (deterministisk): visar förutsägbar och säker exekvering.
3. Guardrail-fråga: visar att osäkra frågor blockeras.
4. Skapa ärende med `confirm=True`: visar kontrollerad mutation.

## Nyckelmening
"Jag använder LLM där resonemang behövs, men håller operationella steg deterministiska och policy-styrda."

## Om de frågar om backend
- "Backend är mockad för stabil demo."
- "TicketAdapter gör byte till Jira/ServiceNow låg-risk."

## Om de frågar om drift
- "Jag loggar `route_selected`, `tool_start`, `tool_end`, `guardrail_blocked`, `policy_blocked`, `agent_error`."

## Om de frågar om tradeoffs
- "Jag prioriterade stabil och förklarbar demo framför bred feature-yta."

## Exit line
"Det här är en medvetet enkel men produktionsnära agent: säkra kontrollvägar, tydlig policy och enkel väg till riktig integration."
