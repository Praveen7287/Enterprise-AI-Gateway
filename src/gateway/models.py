from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[Message] = Field(min_length=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=8192)


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    model: str
    content: str
    provider: str
    usage: Usage
    estimated_cost: float
    fallback_used: bool = False
