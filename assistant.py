from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google import genai

from tools import AuditReportGenerator, AuditTrail, LedgerManager, PythonCodeInterpreter, WebSearcher


@dataclass(frozen=True, slots=True)
class AssistantResult:
    intent: str
    response: str
    operations: list[dict[str, Any]]
    report_path: str | None = None


class GeminiOrchestrator:
    """Translate user text into validated tool commands and execute them."""

    def __init__(self, api_key: str | None = None, report_dir: str = "reports") -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "dummy-gemini-api-key")
        self.ledger = LedgerManager()
        self.web_searcher = WebSearcher()
        self.interpreter = PythonCodeInterpreter()
        self.audit_trail = AuditTrail()
        self.report_generator = AuditReportGenerator(report_dir)

    async def process(self, query: str) -> AssistantResult:
        plan = await self._translate(query)
        intent = str(plan.get("intent", "unknown"))
        operations: list[dict[str, Any]] = []
        for command in plan.get("commands", []):
            operations.append(await self._execute(command))
        response = str(plan.get("response", "Operation completed."))
        report_path = None
        if operations:
            report_path = str(self._write_report(query, operations))
        return AssistantResult(
            intent=intent, response=response, operations=operations, report_path=report_path
        )

    def _write_report(self, query: str, operations: list[dict[str, Any]]) -> Path:
        """Write a PDF audit report covering the entries of the completed transaction."""
        entries = self.audit_trail.retrieve()[-len(operations):]
        return self.report_generator.generate(
            entries, uuid.uuid4().hex[:12], query, self.ledger.snapshot()
        )

    async def _translate(self, query: str) -> dict[str, Any]:
        if self.api_key.startswith("dummy-"):
            return {
                "intent": "unavailable",
                "commands": [],
                "response": "Gemini is not configured. Set GEMINI_API_KEY to enable command translation.",
            }
        client = genai.Client(api_key=self.api_key)
        prompt = (
            "Translate the user request into JSON only. Allowed commands are: "
            "ledger_create{name,value}, ledger_update{name,value}, ledger_retrieve{name}, "
            "calculate{code}, web_search{query}, audit_retrieve{operation}. "
            "Return {intent, commands, response}. Never invent commands. User request: " + query
        )
        result = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return json.loads(result.text)

    async def _execute(self, command: dict[str, Any]) -> dict[str, Any]:
        name = command.get("name")
        arguments = command.get("arguments", {})
        if not isinstance(name, str) or not isinstance(arguments, dict):
            raise ValueError("Invalid tool command")
        if name == "ledger_create":
            output = self.ledger.create(arguments["name"], arguments["value"])
        elif name == "ledger_update":
            output = self.ledger.update(arguments["name"], arguments["value"])
        elif name == "ledger_retrieve":
            output = self.ledger.retrieve(arguments["name"])
        elif name == "calculate":
            output = self.interpreter.execute(arguments["code"], self.ledger.snapshot())
        elif name == "web_search":
            output = await self.web_searcher.search(arguments["query"])
        elif name == "audit_retrieve":
            output = self.audit_trail.retrieve(arguments.get("operation"))
        else:
            raise ValueError(f"Unknown tool command: {name}")
        self.audit_trail.record(name, arguments, output)
        return {"tool": name, "output": output}
