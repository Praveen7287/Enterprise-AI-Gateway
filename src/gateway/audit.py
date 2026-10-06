from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class AuditLog:
    """In-memory metadata-only audit sink for the reference project."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, **event: Any) -> None:
        # Deliberately do not persist prompts, completions, bearer tokens,
        # API keys, or provider secrets in this demo audit record.
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event,
        })

    def list_events(self) -> list[dict[str, Any]]:
        return list(self.events)
