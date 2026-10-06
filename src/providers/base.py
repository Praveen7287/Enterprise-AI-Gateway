from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderResult:
    content: str
    prompt_tokens: int
    completion_tokens: int


class ProviderError(RuntimeError):
    """Provider failure that can be handled by gateway resilience logic."""


class ChatProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, *, model: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> ProviderResult:
        raise NotImplementedError
