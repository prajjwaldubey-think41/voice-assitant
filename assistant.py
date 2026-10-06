from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

from google import genai

from tools import AuditTrail, LedgerManager, PythonCodeInterpreter, WebSearcher


@dataclass(frozen=True, slots=True)
class AssistantResult:
    intent: str
    response: str
    operations: list[dict[str, Any]]


class GeminiOrchestrator:
    """Translate user text into validated tool commands and execute them."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "dummy-gemini-api-key")
        self.ledger = LedgerManager()
        self.web_searcher = WebSearcher()
        self.interpreter = PythonCodeInterpreter()
        self.audit_trail = AuditTrail()

    async def process(self, query: str) -> AssistantResult:
        plan = await self._translate(query)
        intent = str(plan.get("intent", "unknown"))
        operations: list[dict[str, Any]] = []
        for command in plan.get("commands", []):
            operations.append(await self._execute(command))
        response = str(plan.get("response", "Operation completed."))
        return AssistantResult(intent=intent, response=response, operations=operations)

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
