"""Append-only in-process audit trail for foundation work."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    actor_id: str
    details: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditLog:
    def __init__(self):
        self._events: list[AuditEvent] = []

    def record(self, event_type: str, actor_id: str, details: dict | None = None) -> AuditEvent:
        event = AuditEvent(event_type, actor_id, details or {})
        self._events.append(event)
        return event

    def all(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)
