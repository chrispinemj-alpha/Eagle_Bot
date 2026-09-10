"""Work orders: intent first, execution only after governance permits it."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class WorkOrder:
    owner_id: str
    objective: str
    coworker: str = "generalist"
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "queued"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def validate(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective is required")
        if self.status not in {"queued", "running", "blocked", "completed", "failed", "cancelled"}:
            raise ValueError("invalid work order status")
