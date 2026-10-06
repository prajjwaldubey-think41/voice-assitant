from __future__ import annotations

from typing import Any

class LedgerManager:
    """In-memory named-variable store for one assistant session."""

    def __init__(self) -> None:
        self._variables: dict[str, Any] = {}

    def create(self, name: str, value: Any) -> Any:
        if name in self._variables:
            raise ValueError(f"Variable already exists: {name}")
        self._variables[name] = value
        return value

    def update(self, name: str, value: Any) -> Any:
        if name not in self._variables:
            raise KeyError(f"Variable does not exist: {name}")
        self._variables[name] = value
        return value

    def retrieve(self, name: str) -> Any:
        if name not in self._variables:
            raise KeyError(f"Variable does not exist: {name}")
        return self._variables[name]

    def snapshot(self) -> dict[str, Any]:
        return dict(self._variables)
