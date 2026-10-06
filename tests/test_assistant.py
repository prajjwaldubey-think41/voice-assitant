import pytest

from assistant import GeminiOrchestrator
from tools.python_code_interpreter import PythonCodeInterpreter


def test_calculation_can_use_ledger_variables() -> None:
    interpreter = PythonCodeInterpreter()
    assert interpreter.execute("amount * 2", {"amount": 21}) == 42


def test_interpreter_rejects_imports() -> None:
    with pytest.raises(ValueError):
        PythonCodeInterpreter().execute("__import__('os')")


@pytest.mark.asyncio
async def test_dummy_gemini_key_returns_configuration_result() -> None:
    result = await GeminiOrchestrator(api_key="dummy-gemini-api-key").process("what is 2 + 2")
    assert result.intent == "unavailable"
    assert result.operations == []
