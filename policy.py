from __future__ import annotations

import ast
import json
import re
from typing import Any

from guardrails import PROMPT_INJECTION_PATTERNS, TOOL_EXFILTRATION_PATTERNS, normalize_text


class ToolPolicyError(Exception):
    """Raised when a tool call violates policy."""


ALLOWED_TOOLS = {
    "retrieve_incident_info",
    "calculate",
    "create_ticket",
    "get_ticket_status",
    "update_ticket_status",
}

MUTATION_TOOLS = {"create_ticket", "update_ticket_status"}

MUTATION_INTENT_HINTS = {
    "create_ticket": [
        "create ticket",
        "new ticket",
        "open ticket",
        "create incident",
        "open incident",
        "skapa ärende",
        "öppna ärende",
        "skapa incident",
        "skapa ett nytt ärende",
        "skapa nytt ärende",
    ],
    "update_ticket_status": [
        "update ticket",
        "change status",
        "set status",
        "resolve ticket",
        "close ticket",
        "update incident",
        "uppdatera ärende",
        "ändra status",
        "sätt status",
        "stäng ärende",
        "lös ärende",
        "uppdatera incident",
    ],
}


def policy_refusal(code: str, message: str, tool_name: str) -> str:
    return json.dumps(
        {
            "type": "policy_refusal",
            "code": code,
            "message": message,
            "tool": tool_name,
            "action": "blocked",
        }
    )


def has_explicit_intent(user_input: str, tool_name: str) -> bool:
    hints = MUTATION_INTENT_HINTS.get(tool_name, [])
    lower = normalize_text(user_input)
    return any(h in lower for h in hints)


def parse_structured_tool_input(tool_input: Any) -> dict[str, Any] | None:
    if isinstance(tool_input, dict):
        return tool_input

    if not isinstance(tool_input, str):
        return None

    text = tool_input.strip()
    if not text:
        return None

    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(text)
        except Exception:
            continue
        if isinstance(parsed, dict):
            return parsed

    return None


def confirm_is_true(tool_input: Any) -> bool:
    if isinstance(tool_input, bool):
        return tool_input

    parsed = parse_structured_tool_input(tool_input)
    if parsed is not None:
        confirm_value = parsed.get("confirm")
        if isinstance(confirm_value, bool):
            return confirm_value
        if isinstance(confirm_value, str):
            return normalize_text(confirm_value) == "true"

    text = normalize_text(str(tool_input or ""))
    match = re.search(r"\bconfirm\s*[:=]\s*(true|false)\b", text)
    return bool(match and match.group(1) == "true")


def enforce_tool_policy(tool_name: str, tool_input: Any, user_input: str) -> None:
    if tool_name not in ALLOWED_TOOLS:
        raise ToolPolicyError(
            policy_refusal("TOOL_NOT_ALLOWED", f"Tool '{tool_name}' is not in the allowlist.", tool_name)
        )

    combined_text = normalize_text(f"{user_input}\n{tool_input}")
    exfiltration_patterns = TOOL_EXFILTRATION_PATTERNS + PROMPT_INJECTION_PATTERNS
    for pattern in exfiltration_patterns:
        if pattern in combined_text:
            raise ToolPolicyError(
                policy_refusal(
                    "EXFILTRATION_ATTEMPT",
                    "Request appears to target prompts, secrets, or credentials.",
                    tool_name,
                )
            )

    if tool_name in MUTATION_TOOLS and not has_explicit_intent(user_input, tool_name):
        raise ToolPolicyError(
            policy_refusal(
                "MUTATION_INTENT_UNCLEAR",
                "Mutation tool call blocked because user intent is not explicit.",
                tool_name,
            )
        )

    if tool_name in MUTATION_TOOLS and not confirm_is_true(tool_input):
        raise ToolPolicyError(
            policy_refusal(
                "CONFIRMATION_REQUIRED",
                "Mutation tool call requires confirm=True.",
                tool_name,
            )
        )
