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


@pytest.mark.asyncio
async def test_completed_transaction_generates_pdf_report(tmp_path) -> None:
    orchestrator = GeminiOrchestrator(api_key="dummy-gemini-api-key", report_dir=str(tmp_path))

    async def fake_translate(query: str) -> dict:
        return {
            "intent": "ledger",
            "commands": [{"name": "ledger_create", "arguments": {"name": "amount", "value": 5}}],
            "response": "done",
        }

    orchestrator._translate = fake_translate
    result = await orchestrator.process("create amount 5")
    assert result.report_path is not None
    assert open(result.report_path, "rb").read().startswith(b"%PDF")


@pytest.mark.asyncio
async def test_no_report_when_no_operations(tmp_path) -> None:
    orchestrator = GeminiOrchestrator(api_key="dummy-gemini-api-key", report_dir=str(tmp_path))
    result = await orchestrator.process("hello")
    assert result.report_path is None
    assert list(tmp_path.iterdir()) == []
