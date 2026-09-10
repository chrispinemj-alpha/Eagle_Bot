"""Boundary for real-world information providers.

No provider is assumed here. A provider must explicitly return evidence metadata.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    source: str
    claim: str
    retrieved_at: str
    confidence: str = "unknown"


class WorldGateway:
    def __init__(self, provider=None):
        self.provider = provider

    def search(self, query: str):
        if not self.provider:
            raise RuntimeError("No world-information provider configured")
        return self.provider.search(query)
