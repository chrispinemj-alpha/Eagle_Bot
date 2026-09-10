"""Identity primitives for Eagle users and organizations."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Identity:
    id: str = field(default_factory=lambda: str(uuid4()))
    kind: str = "human"
    display_name: str = ""
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        if self.kind not in {"human", "organization", "agent"}:
            raise ValueError("identity kind must be human, organization, or agent")
        if not self.display_name.strip():
            raise ValueError("display_name is required")
