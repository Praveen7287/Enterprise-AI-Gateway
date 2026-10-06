from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status

from gateway.audit import AuditLog
from gateway.config import FEATURE_ROUTES, PROVIDERS
from gateway.models import ChatCompletionRequest, ChatCompletionResponse, Usage
from gateway.policies import PolicyEngine, Principal
from providers.base import ChatProvider, ProviderError


class AIGatewayService:
    """Orchestrates gateway controls without becoming an agent orchestrator."""

    def __init__(self, providers: dict[str, ChatProvider], policy: PolicyEngine, audit: AuditLog) -> None:
        self.providers = providers
        self.policy = policy
        self.audit = audit

    async def chat(self, *, principal: Principal, feature: str, request: ChatCompletionRequest) -> ChatCompletionResponse:
        self.policy.validate_license(feature)
        self.policy.authorize(principal, feature)

        estimated_prompt_tokens = max(1, sum(len(m.content.split()) for m in request.messages))
        requested_tokens = estimated_prompt_tokens + request.max_tokens
        self.policy.reserve_tokens(requested_tokens)

        selected_model = request.model or PROVIDERS[FEATURE_ROUTES[feature][0]].model
        errors: list[str] = []
        fallback_used = False

        try:
            for index, provider_name in enumerate(FEATURE_ROUTES.get(feature, FEATURE_ROUTES["default"])):
                provider = self.providers.get(provider_name)
                if provider is None:
                    errors.append(f"{provider_name}: not configured")
                    continue

                try:
                    config = PROVIDERS[provider_name]
                    result = await provider.complete(
                        model=request.model or config.model,
                        messages=[m.model_dump() for m in request.messages],
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                    )
                    fallback_used = index > 0
                    total = result.prompt_tokens + result.completion_tokens
                    cost = (total / 1000.0) * config.cost_per_1k_tokens
                    self.policy.release_tokens(requested_tokens)
                    self.policy.reserve_tokens(total)

                    self.audit.record(
                        event="chat.completion",
                        request_id=str(uuid4()),
                        subject=principal.subject,
                        role=principal.role,
                        feature=feature,
                        provider=provider_name,
                        model=request.model or config.model,
                        total_tokens=total,
                        fallback_used=fallback_used,
                    )

                    return ChatCompletionResponse(
                        id=f"chatcmpl-{uuid4().hex}",
                        model=request.model or config.model,
                        content=result.content,
                        provider=provider_name,
                        usage=Usage(
                            prompt_tokens=result.prompt_tokens,
                            completion_tokens=result.completion_tokens,
                            total_tokens=total,
                        ),
                        estimated_cost=round(cost, 6),
                        fallback_used=fallback_used,
                    )
                except ProviderError as exc:
                    errors.append(f"{provider_name}: unavailable")
                    continue
        finally:
            # Return the reservation to the demo budget. A production system
            # would reconcile usage against a durable quota/ledger.
            self.policy.release_tokens(requested_tokens)

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No AI provider is currently available",
        )
