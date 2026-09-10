"""Provider-neutral AI gateway. No model vendor is hard-coded into Eagle Core."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AIResponse:
    text: str
    provider: str
    model: str
    evidence: tuple = ()


class AIProvider(Protocol):
    def generate(self, prompt: str, **kwargs) -> AIResponse: ...


class AIGateway:
    def __init__(self, provider: AIProvider | None = None):
        self.provider = provider

    def generate(self, prompt: str, **kwargs) -> AIResponse:
        if not self.provider:
            raise RuntimeError("No AI provider configured")
        return self.provider.generate(prompt, **kwargs)
