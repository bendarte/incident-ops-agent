# guardrails.py
import re
import unicodedata

# Zero-width-tecken som används för att kringgå nyckelordsmatchning (t.ex. "api\u200bkey")
_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def normalize_text(text: str) -> str:
    """NFKD-normalisera, ta bort zero-width-tecken och lowercase.

    Fångar helbreddstecken (ａｐｉ → api), ligaturer och
    zero-width-trick som används för att undvika nyckelordsmatchning.
    """
    text = unicodedata.normalize("NFKD", text or "")
    text = _ZERO_WIDTH.sub("", text)
    return text.lower()


# --- Blockerade mönster grupperade efter kategori ---

_DESTRUCTIVE = [
    "delete all data", "radera all data",
    "format hard drive", "formatera hårddisk",
    "transfer money", "överför pengar",
    "drop table", "rm -rf",
    "wipe all", "rensa allt",
]

_PROMPT_INJECTION = [
    "system prompt", "systemprompt",
    "reveal your instructions", "visa dina instruktioner",
    "show me your hidden prompt", "visa din dolda prompt",
    "ignore previous instructions", "ignorera tidigare instruktioner",
    "forget your instructions", "glöm dina instruktioner",
    "you are now", "du är nu",
    "pretend you are", "låtsas att du är",
    "act as if you", "agera som om du",
    "disregard your", "bortse från dina",
    "new persona", "ny persona",
    "override instructions", "åsidosätt instruktioner",
]

SECRET_EXTRACTION_PATTERNS = [
    "api key", "api-nyckel", "api_key",
    "password", "lösenord",
    "secret", "hemlighet",
    "private key", "privat nyckel",
    "access key", "åtkomstnyckel",
    "disclose", "avslöja",
    "leak your", "läcka dina",
    "divulge", "röja",
    "expose your", "avslöja dina",
    "exfiltrate",
]

PROMPT_INJECTION_PATTERNS = list(_PROMPT_INJECTION)

# Verktygspolicy ska vara snävare än input-guardrailen för att undvika breda false positives.
TOOL_EXFILTRATION_PATTERNS = [
    "system prompt", "systemprompt",
    "hidden prompt", "dolda instruktioner",
    "api key", "api-nyckel", "api_key",
    "password", "lösenord",
    "secret", "hemlighet",
    "private key", "privat nyckel",
    "access key", "åtkomstnyckel",
    "client secret", "bearer token", "api token", "auth token",
]

BLOCKED_KEYWORDS = _DESTRUCTIVE + _PROMPT_INJECTION + SECRET_EXTRACTION_PATTERNS

OUT_OF_SCOPE_HINTS = [
    "write a poem", "skriv en dikt",
    "tell me a joke", "berätta ett skämt",
    "roast",
]

# Regex för vanliga API-nyckel-/tokenformat i output
_SECRET_PATTERN = re.compile(r"sk-[a-z0-9_\-]{20,}")


def input_guardrail(prompt: str) -> bool:
    normalized = normalize_text(prompt)

    for kw in BLOCKED_KEYWORDS:
        if kw in normalized:
            print(f"Guardrail-varning: blockerat nyckelord upptäckt: '{kw}'")
            return False

    for hint in OUT_OF_SCOPE_HINTS:
        if hint in normalized:
            print("Guardrail-varning: out-of-scope-fråga för en incident/ops-agent.")
            return False

    return True


def output_guardrail(output: str, initial_prompt: str) -> bool:
    out = normalize_text(output)

    # PII-mönster
    if "social security number" in out or "ssn" in out or "personnummer" in out:
        print("Guardrail-varning: möjlig PII upptäckt.")
        return False

    # API-nyckel-/tokenformat
    if _SECRET_PATTERN.search(out):
        print("Guardrail-varning: möjlig API-nyckel i output.")
        return False

    # Om användarens intent var att extrahera hemligheter eller injicera prompt — blockera alltid
    ip = normalize_text(initial_prompt)
    if any(kw in ip for kw in SECRET_EXTRACTION_PATTERNS + _PROMPT_INJECTION):
        return False

    return True
