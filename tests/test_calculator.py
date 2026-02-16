from tools import calculate


def test_calculate_basic_expression():
    assert calculate.invoke("(10 + 20 + 30) / 3") == "20"


def test_calculate_rejects_unsafe_expression():
    out = calculate.invoke("__import__('os').system('echo hi')")
    assert out.startswith("Error evaluating expression:")
