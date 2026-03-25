import main


class _DummyCalculateTool:
    name = "calculate"

    @staticmethod
    def invoke(_expression):
        return "26"


class _DummyUpdateTicketTool:
    name = "update_ticket_status"
    calls = []

    @classmethod
    def invoke(cls, payload):
        cls.calls.append(payload)
        return f"Ticket '{payload['ticket_id']}' status updated to '{payload['new_status']}'."


def test_deterministic_route_handles_swedish_calculation_prompt(monkeypatch):
    monkeypatch.setattr(main, "enforce_tool_policy", lambda **kwargs: None)
    monkeypatch.setattr(main, "calculate", _DummyCalculateTool())

    result = main.run_deterministic_route("Beräkna (18 + 24 + 36) / 3")

    assert result == "26"


def test_deterministic_route_handles_combining_diacritic(monkeypatch):
    monkeypatch.setattr(main, "enforce_tool_policy", lambda **kwargs: None)
    monkeypatch.setattr(main, "calculate", _DummyCalculateTool())

    # 'a' + combining diaeresis, which can occur depending on keyboard/input method.
    result = main.run_deterministic_route("Bera\u0308kna (18 + 24 + 36) / 3")

    assert result == "26"


def test_deterministic_route_updates_ticket_status(monkeypatch):
    _DummyUpdateTicketTool.calls = []
    monkeypatch.setattr(main, "enforce_tool_policy", lambda **kwargs: None)
    monkeypatch.setattr(main, "update_ticket_status", _DummyUpdateTicketTool)

    result = main.run_deterministic_route('Update ticket INC-7 status: "Resolved" confirm=True')

    assert "INC-7" in result
    assert _DummyUpdateTicketTool.calls == [
        {"ticket_id": "INC-7", "new_status": "Resolved", "confirm": True}
    ]
