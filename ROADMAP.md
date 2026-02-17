# Roadmap (Interview-Focused)

## Phase 1: Next 1 Day
- Stabil setup:
  - Säkerställ reproducibel miljö (`.venv`, pinned dependencies, fungerande pytest-installation).
- Bas-observability:
  - Lägg enkel strukturerad loggning (JSON) för request, routed path (deterministic/LLM), tool-call, policy decisions.
- Säkerhetshygien:
  - Flytta policy-konstanter till tydlig konfigurationssektion med versionerad policy-id.

## Phase 2: Next 1 Week
- API integration idea:
  - Byt mock ticket-system mot adapter för Jira/ServiceNow med idempotency key, timeout, retry och tydliga felkoder.
- Structured logging/telemetry:
  - Spåra latency per steg, verktygsfel, refusal-rate, tokenkostnad och success-rate.
- Stronger policy engine:
  - Ersätt enkla pattern checks med regelmotor per verktyg/intention (policy-as-data), inklusive audit reason codes.
- Safe FAISS handling:
  - Lägg integrity checks för indexfiler, versionering av embeddings/index och säker rebuild-fallback.

## Phase 3: Next 1 Month
- Eval harness:
  - Bygg ett lätt eval-ramverk med representativa incidentfrågor, policy-testfall, determinism-checkar och regressionsrapport.
- RAG quality improvements:
  - Query rewrite, hybrid retrieval och bättre source attribution/confidence scoring.
- Production hardening:
  - RBAC för muterande actions, rate limiting, circuit breaker mot externa API:er och tydlig incident run-mode.
- Operativ mognad:
  - Dashboard för kvalitet/säkerhet (tool success, policy blocks, false positives, p95 latency).
