# guardrails.py

BLOCKED_KEYWORDS = [
    "delete all data",
    "format hard drive",
    "transfer money",
    "system prompt",
    "reveal your instructions",
    "show me your hidden prompt",
    "api key",
    "password",
    "secret",
]

OUT_OF_SCOPE_HINTS = [
    "write a poem",
    "tell me a joke",
    "roast",
]

def input_guardrail(prompt: str) -> bool:
    prompt_lower = (prompt or "").lower()

    for kw in BLOCKED_KEYWORDS:
        if kw in prompt_lower:
            print(f"Guardrail Alert: blocked keyword detected: '{kw}'")
            return False

    for hint in OUT_OF_SCOPE_HINTS:
        if hint in prompt_lower:
            print("Guardrail Alert: out-of-scope request for an incident/ops agent.")
            return False

    return True


def output_guardrail(output: str, initial_prompt: str) -> bool:
    out = (output or "").lower()

    # Very basic PII/secret hints (demo-level)
    if "social security number" in out or "ssn" in out:
        print("Guardrail Alert: possible PII detected.")
        return False

    # If user asks for secrets/system prompt, refuse
    ip = (initial_prompt or "").lower()
    if "system prompt" in ip or "api key" in ip or "secret" in ip:
        return False

    return True
