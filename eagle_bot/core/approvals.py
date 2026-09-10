"""Human-in-the-loop approval records."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class Approval:
    request_id: str
    approved_by: str
    decision: str
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def validate(self) -> None:
        if self.decision not in {"approved", "rejected"}:
            raise ValueError("decision must be approved or rejected")
