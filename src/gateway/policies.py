from __future__ import annotations

from dataclasses import dataclass
from fastapi import HTTPException, status

from .config import FEATURE_LICENSES, ROLE_FEATURES, TOKEN_BUDGET, TOKENS


@dataclass(frozen=True)
class Principal:
    subject: str
    role: str


class PolicyEngine:
    """Small policy layer illustrating gateway control-plane decisions."""

    def __init__(self, token_budget: int = TOKEN_BUDGET) -> None:
        self.token_budget = token_budget
        self._reserved = 0

    def authenticate(self, authorization: str | None) -> Principal:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        token = authorization.split(" ", 1)[1].strip()
        role = TOKENS.get(token)
        if not role:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return Principal(subject=f"demo-{role}", role=role)

    def authorize(self, principal: Principal, feature: str) -> None:
        allowed = ROLE_FEATURES.get(principal.role, set())
        if feature not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Feature not authorized")

    def validate_license(self, feature: str) -> None:
        # Demonstrates the decision point. A real implementation would query
        # a durable entitlement/license service.
        if feature not in FEATURE_LICENSES:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Feature not licensed")

    def require_admin(self, principal: Principal) -> None:
        if principal.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    def reserve_tokens(self, requested: int) -> None:
        if self._reserved + requested > self.token_budget:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Token budget exceeded")
        self._reserved += requested

    def release_tokens(self, actual: int) -> None:
        self._reserved = max(0, self._reserved - actual)
