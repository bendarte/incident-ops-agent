📘 Incident Ops Agent – Förklaring av Arkitektur
🧠 Översikt
Detta projekt är en AI-baserad driftassistent som körs i terminalen.
Den kombinerar:
📚 Interna dokument (incidentrapporter och runbooks)
🔎 Semantisk sökning via embeddings (RAG)
🤖 OpenAI för språkförståelse och svarsgenerering
🛠 Verktyg (kalkylator, ticket-system)
🛡 Guardrails för säkerhet
Det är inte en vanlig chatbot – det är ett system som kan både läsa, resonera och agera.
🔁 Vad händer när programmet startar?
När du kör:
python main.py chat
sker följande:
Programmet laddar din OpenAI API-nyckel.
Det skapar en koppling till OpenAI-modellen.
Det registrerar alla verktyg (RAG, kalkylator, tickets).
Det startar en interaktiv loop där du kan ställa frågor.
Agenten är nu redo att ta emot kommandon.
📁 Var finns kunskapen?
All intern kunskap ligger i mappen:
corpus/
Exempel:
corpus/
  incident_db_latency.txt
  runbook_web_cpu_spike.txt
Det är dessa filer som agenten använder för att svara på frågor.
OpenAI har inte direkt tillgång till dessa filer.
De läses lokalt av din kod.
🔎 Vad är RAG?
RAG står för:
Retrieval Augmented Generation
Det betyder:
Systemet letar först upp relevant information i dina dokument.
Sedan använder det OpenAI för att formulera ett tydligt svar.
Steg för steg när du frågar om latency:
Frågan omvandlas till en embedding (en matematisk representation).
FAISS jämför den med embeddings från dina dokument.
Den hittar den mest relevanta textbiten.
Den texten skickas till OpenAI.
OpenAI skriver ett tydligt svar baserat på den texten.
Systemet hittar alltså inte på – det arbetar dokumentbaserat.
🧮 Vad är embeddings?
Embeddings är ett sätt att översätta språk till matematik.
Varje mening omvandlas till en lista med siffror som representerar dess betydelse.
När man ställer en fråga omvandlas även den till siffror, och systemet letar efter den text som matematiskt ligger närmast frågan.
Det är så AI:n hittar rätt information utan att matcha exakta ord.
🗄 Vad är FAISS?
FAISS är en vektordatabas.
Den lagrar embeddings och kan snabbt hitta:
“Vilken text är mest lik den här frågan?”
Det är därför systemet kan göra semantisk sökning istället för vanlig ordsökning.
🛠 Verktyg
Agenten har flera verktyg:
📚 retrieve_incident_info
Söker i corpus/
Hämtar relevanta textbitar
Returnerar text + källor
🧮 calculate
Räknar matematiska uttryck
Säker implementation (ingen farlig eval)
🎫 Ticket-system
Skapar incidenter
Hämtar status
Uppdaterar status
Kräver bekräftelse vid känsliga åtgärder
I projektet är tickets simulerade (mockade),
men i en verklig miljö skulle dessa anropa riktiga API:er som Jira eller ServiceNow.
🛡 Guardrails
Guardrails skyddar systemet från:
Att avslöja systemprompt
Att läcka hemligheter
Att utföra skadliga kommandon
Det är ett säkerhetslager mellan användaren och modellen.
🏗 Arkitektur i lager
Projektet består av fyra lager:
Data-lager → corpus/
Retrieval-lager → Embeddings + FAISS
Resonemangs-lager → OpenAI
Action-lager → Verktyg (tickets, kalkylator)
Detta är en generell AI-agent-arkitektur som kan återanvändas i andra projekt.
🎯 Sammanfattning
Detta projekt är en AI-driven incidentassistent som:
Läser interna dokument
Använder semantisk sökning
Formulerar svar med OpenAI
Kan agera genom verktyg
Har inbyggd säkerhet
Det är en mini-version av hur enterprise AI-system byggs i verkligheten.