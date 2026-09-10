"""Initial governed coworker registry. These are roles, not claims of intelligence."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Coworker:
    key: str
    name: str
    purpose: str


INITIAL_COWORKERS = (
    Coworker("generalist", "Generalist", "Understands goals and coordinates work."),
    Coworker("researcher", "Researcher", "Researches, evaluates evidence and synthesizes knowledge."),
    Coworker("builder", "Builder", "Plans and implements software and systems."),
    Coworker("analyst", "Analyst", "Performs analysis and supports decisions."),
    Coworker("operator", "Operator", "Coordinates permitted workflows and operational execution."),
    Coworker("educator", "Educator", "Teaches, explains and supports learning."),
)


class CoworkerRegistry:
    def __init__(self, coworkers=INITIAL_COWORKERS):
        self._coworkers = {c.key: c for c in coworkers}

    def get(self, key: str) -> Coworker:
        try:
            return self._coworkers[key]
        except KeyError as exc:
            raise KeyError(f"unknown coworker: {key}") from exc

    def list(self):
        return tuple(self._coworkers.values())
