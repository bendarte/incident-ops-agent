# guardrails.py

BLOCKED_KEYWORDS = [
    "delete all data",
    "radera all data",
    "format hard drive",
    "formatera hårddisk",
    "transfer money",
    "överför pengar",
    "system prompt",
    "systemprompt",
    "reveal your instructions",
    "visa dina instruktioner",
    "show me your hidden prompt",
    "visa din dolda prompt",
    "api key",
    "api-nyckel",
    "password",
    "lösenord",
    "secret",
    "hemlighet",
]

OUT_OF_SCOPE_HINTS = [
    "write a poem",
    "skriv en dikt",
    "tell me a joke",
    "berätta ett skämt",
    "roast",
]

def input_guardrail(prompt: str) -> bool:
    prompt_lower = (prompt or "").lower()

    for kw in BLOCKED_KEYWORDS:
        if kw in prompt_lower:
            print(f"Guardrail-varning: blockerat nyckelord upptäckt: '{kw}'")
            return False

    for hint in OUT_OF_SCOPE_HINTS:
        if hint in prompt_lower:
            print("Guardrail-varning: out-of-scope-fråga för en incident/ops-agent.")
            return False

    return True


def output_guardrail(output: str, initial_prompt: str) -> bool:
    out = (output or "").lower()

    # Very basic PII/secret hints (demo-level)
    if "social security number" in out or "ssn" in out or "personnummer" in out:
        print("Guardrail-varning: möjlig PII upptäckt.")
        return False

    # If user asks for secrets/system prompt, refuse
    ip = (initial_prompt or "").lower()
    if (
        "system prompt" in ip
        or "systemprompt" in ip
        or "api key" in ip
        or "api-nyckel" in ip
        or "secret" in ip
        or "hemlighet" in ip
    ):
        return False

    return True
