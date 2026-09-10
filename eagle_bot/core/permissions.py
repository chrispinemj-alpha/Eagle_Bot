"""Permission primitives. Default deny for actions that can change external state."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Permission:
    subject_id: str
    action: str
    resource: str


class PermissionChecker:
    def __init__(self):
        self._grants: set[Permission] = set()

    def grant(self, permission: Permission) -> None:
        self._grants.add(permission)

    def allowed(self, subject_id: str, action: str, resource: str) -> bool:
        return Permission(subject_id, action, resource) in self._grants
