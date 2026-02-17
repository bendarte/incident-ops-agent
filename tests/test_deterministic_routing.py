import main


class _DummyCalculateTool:
    name = "calculate"

    @staticmethod
    def invoke(_expression):
        return "26"


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
