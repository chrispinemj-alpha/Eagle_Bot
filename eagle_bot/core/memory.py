"""Small, explicit memory layer. Persistence can be replaced by a database later."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class MemoryItem:
    owner_id: str
    content: str
    source: str = "user"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc).isoformat())


class MemoryStore:
    def __init__(self) -> None:
        self._items: list[MemoryItem] = []

    def remember(self, item: MemoryItem) -> MemoryItem:
        if not item.content.strip():
            raise ValueError("memory content cannot be empty")
        self._items.append(item)
        return item

    def recall(self, owner_id: str, limit: int = 20) -> Iterable[MemoryItem]:
        if limit < 1:
            raise ValueError("limit must be positive")
        return [x for x in reversed(self._items) if x.owner_id == owner_id][:limit]
