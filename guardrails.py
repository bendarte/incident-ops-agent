# guardrails.py

def input_guardrail(prompt: str) -> bool:
    """
    Basic input guardrail to check for potentially harmful or out-of-scope requests.
    Returns True if the input is allowed, False otherwise.
    """
    prompt_lower = prompt.lower()
    blocked_keywords = ["delete all data", "format hard drive", "transfer money"]
    for keyword in blocked_keywords:
        if keyword in prompt_lower:
            print(f"Guardrail Alert: Input contains blocked keyword: '{keyword}'.")
            return False
    
    # Example: Disallow requests that are clearly not incident/ops related
    if "write a poem" in prompt_lower or "tell me a joke" in prompt_lower:
        print("Guardrail Alert: Input seems out of scope for incident/ops agent.")
        return False
        
    return True

def output_guardrail(output: str, initial_prompt: str) -> bool:
    """
    Basic output guardrail to check the agent's response for safety or confirmation.
    Returns True if the output is allowed, False otherwise.
    """
    output_lower = output.lower()

    # Example: If the original prompt was about creating a ticket, ensure the output confirms it.
    if "create ticket" in initial_prompt.lower():
        if "ticket created successfully" not in output_lower:
            print("Guardrail Alert: Expected ticket creation confirmation not found in output.")
            # This guardrail could be adjusted to return False to block the output
            # but for a demo, we might just warn.
            # return False
            pass # Allow for now, just warn

    # Example: Check for any PII if relevant (requires more advanced logic, placeholder here)
    if "ssn" in output_lower or "social security number" in output_lower:
        print("Guardrail Alert: Output might contain sensitive PII.")
        return False # Block output if PII is detected

    return True

