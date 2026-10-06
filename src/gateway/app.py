from __future__ import annotations

from fastapi import Depends, FastAPI, Header

from gateway.audit import AuditLog
from gateway.config import PROVIDERS
from gateway.models import ChatCompletionRequest, ChatCompletionResponse
from gateway.policies import PolicyEngine
from gateway.service import AIGatewayService
from providers.mock import MockProvider


app = FastAPI(
    title="Enterprise AI Gateway",
    version="1.0.0",
    description="Reference implementation of an enterprise AI control plane.",
)

audit = AuditLog()
policy = PolicyEngine()
providers = {
    name: MockProvider(name)
    for name in PROVIDERS
}
service = AIGatewayService(providers=providers, policy=policy, audit=audit)


def principal_from_header(authorization: str | None = Header(default=None)):
    return policy.authenticate(authorization)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    x_ai_feature: str = Header(default="default", alias="X-AI-Feature"),
    principal=Depends(principal_from_header),
) -> ChatCompletionResponse:
    return await service.chat(principal=principal, feature=x_ai_feature, request=request)


@app.get("/admin/audit")
async def get_audit(principal=Depends(principal_from_header)) -> dict:
    policy.require_admin(principal)
    return {"events": audit.list_events()}
