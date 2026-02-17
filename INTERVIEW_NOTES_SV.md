# Interview Notes (SV)

## 60-sekunders pitch
Det här är en Incident Ops-agent byggd med LangChain ReAct, verktyg och ett lokalt RAG-lager. Jag separerade deterministiska operationer från LLM-resonemang: tydliga kommandon som ticket-status och beräkningar går direkt till verktyg, medan otydliga frågor går via modellen. Jag lade också policykontroller vid verktygsgränsen, inte bara i prompttext, med allowlist, mutationsskydd och strukturerade blockeringar. Resultatet är en liten men tydlig arkitektur med bättre driftssäkerhet, säkerhetstänk och förklarbarhet.

## 2-minuters pitch
Projektet är medvetet litet men visar produktionsnära AI engineering:
1. ReAct-agent för resonemang och verktygsval.
2. Verktyg för RAG, kalkylator och ticket-hantering.
3. RAG över lokala incident/runbook-filer med FAISS-cache.
4. Guardrails + policy gates för säkerhet.

Dataflöde: användarfråga -> input-guardrail -> deterministisk router (om tydligt case) -> annars ReAct-agent -> verktyg -> output-guardrail -> svar.

Det viktiga designvalet var att LLM inte styr allt. Kritiska och deterministiska operationer går direkt till verktyg för att minska latens, kostnad och oförutsägbart beteende. Jag lade även policy enforcement vid action boundary, alltså precis innan verktyg körs. Där kan jag stoppa exfiltration/prompt-injection-försök och kräva explicit intention + confirm=True vid mutationer.

Jag lade till fail-fast startup checks och lean tester för guardrails, kalkylator och ticket-livscykel. Fokus är hög signal, inte test-teater. Det här gör projektet lätt att förklara i intervju: liten kodbas, tydliga tradeoffs, och tydliga säkerhets- och tillförlitlighetsval.

## Arkitektur: ReAct + Tools + RAG + Guardrails
- ReAct-agent: tolkar otydliga frågor, planerar verktygsanrop.
- Tools:
  - `retrieve_incident_info` (RAG)
  - `calculate` (säker AST-baserad matematik)
  - `create_ticket` / `get_ticket_status` / `update_ticket_status`
- RAG:
  - Läser `corpus/*.txt`
  - Embeddings + FAISS
  - Returnerar text + källor
- Guardrails:
  - Input/output-filter
  - Policy gate vid verktygsgräns (allowlist, exfiltration-check, mutationsregler)

## Varför deterministisk control path är viktigt
- Pålitlighet: kritiska operationer blir reproducerbara.
- Lägre latens/kostnad: onödiga LLM-anrop försvinner.
- Mindre risk: färre hallucinationer i operativa kommandon.
- Tydlig ansvarsmodell: LLM för tolkning, kod för kontroll.

## Varför tool-boundary policy gates är viktigt
- Skydd där det spelar roll: precis innan handling sker.
- Svårare att kringgå än rena keyword-filter i prompt.
- Konsekvent enforcement oavsett om anrop kommer från agent eller deterministisk route.
- Strukturerade refusals gör loggning, analys och vidare hantering enklare.

## 8 tuffa intervjufrågor + starka svar
1. **Varför inte låta LLM hantera allt?**
Svar: För operativa system vill jag minimera nondeterminism i kontrollflödet. Jag använder LLM för språkförståelse, inte för state-changing kontroll.

2. **Hur hanterar du prompt injection?**
Svar: Jag blockerar vid verktygsgränsen med policykontroll (allowlist + exfiltration patterns + mutationskrav), inte bara i systemprompten.

3. **Vad är största risken i RAG-delen?**
Svar: Tyst fel vid index/laddning. Därför lade jag tydliga felmeddelanden för embeddings, FAISS-load/build och corpusvalidering.

4. **Hur säkerställer du att tickets inte skapas av misstag?**
Svar: Muterande verktyg kräver `confirm=True` och explicit intent. Annars returneras strukturerad blockering.

5. **Varför ReAct här?**
Svar: ReAct är lätt att förklara och passar små agenter med flera verktyg. Bra balans mellan flexibilitet och enkelhet.

6. **Hur testar du ett LLM-system utan att överbygga?**
Svar: Jag testar deterministiska riskytor hårt (guardrails, kalkylator, ticket-livscykel) och håller LLM-e2e tunt.

7. **Vad skulle du förbättra först i produktion?**
Svar: Strukturerad telemetry, starkare policy engine och riktiga API-integrationer med idempotens/retry.

8. **Hur förklarar du seniority i detta projekt?**
Svar: Genom att visa tydliga tradeoffs: separera resonemang från kontroll, enforce policy vid action boundary, fail-fast vid startup och fokuserad testning.

## Kort demo-script (live)
Kör i repo-roten:

```bash
# 1) Aktivera venv
source .venv/bin/activate

# 2) Installera dependencies (inkl. pytest)
pip install -r requirements.txt

# 3) Kör demo
python3 main.py demo

# 4) Visa deterministisk status-path (ingen LLM behövs)
python3 main.py status INC-1

# 5) Interaktivt test
python3 main.py chat
# Skriv t.ex.:
# Calculate (10 + 20 + 30) / 3
# What is the status of ticket INC-1?
# What is the runbook for web CPU spikes?
```
