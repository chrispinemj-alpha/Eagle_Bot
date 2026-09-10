"""Explicit tool registry. Unknown tools are denied by default."""


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name: str, handler, *, risk: str = "low") -> None:
        if not name.strip():
            raise ValueError("tool name is required")
        self._tools[name] = {"handler": handler, "risk": risk}

    def describe(self) -> list[dict]:
        return [{"name": k, "risk": v["risk"]} for k, v in self._tools.items()]

    def get(self, name: str):
        if name not in self._tools:
            raise KeyError(f"tool is not registered: {name}")
        return self._tools[name]
