from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class AuditEntry:
    operation: str
    input: Any
    output: Any
    timestamp: str


class AuditTrail:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(self, operation: str, input: Any, output: Any) -> AuditEntry:
        entry = AuditEntry(
            operation=operation,
            input=input,
            output=output,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._entries.append(entry)
        return entry

    def retrieve(self, operation: str | None = None) -> list[dict[str, Any]]:
        entries = self._entries
        if operation is not None:
            entries = [entry for entry in entries if entry.operation == operation]
        return [asdict(entry) for entry in entries]
