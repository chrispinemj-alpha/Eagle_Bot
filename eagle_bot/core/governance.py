"""Risk and authorization rules for Eagle actions."""
from enum import Enum
from dataclasses import dataclass


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ActionRequest:
    action: str
    risk: RiskLevel
    requested_by: str
    target: str = ""


class Governance:
    """Conservative default: information is easier to permit than real-world action."""

    def requires_approval(self, request: ActionRequest) -> bool:
        return request.risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}

    def can_execute(self, request: ActionRequest, approved: bool = False) -> bool:
        if request.risk == RiskLevel.CRITICAL:
            return False if not approved else True
        return approved or not self.requires_approval(request)
