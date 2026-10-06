from __future__ import annotations

from .base import ChatProvider, ProviderError, ProviderResult


class MockProvider(ChatProvider):
    """Deterministic provider used for tests and local demonstrations."""

    def __init__(self, name: str, *, available: bool = True) -> None:
        self.name = name
        self.available = available

    async def complete(self, *, model: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> ProviderResult:
        if not self.available:
            raise ProviderError(f"{self.name} provider unavailable")

        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        prompt = user_messages[-1] if user_messages else messages[-1]["content"]
        content = f"Demo response from {self.name}: {prompt}"
        prompt_tokens = max(1, sum(len(m["content"].split()) for m in messages))
        completion_tokens = max(1, len(content.split()))
        return ProviderResult(content, prompt_tokens, completion_tokens)
