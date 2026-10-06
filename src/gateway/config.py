from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    enabled: bool = True
    cost_per_1k_tokens: float = 0.0
    supports_chat: bool = True


# In a production deployment these values should come from a secure configuration
# store / secret manager rather than source control.
PROVIDERS = {
    "local": ProviderConfig("local", "demo-local", cost_per_1k_tokens=0.0),
    "cloud": ProviderConfig("cloud", "demo-cloud", cost_per_1k_tokens=0.002),
}

# Feature -> ordered provider preference list. The first healthy provider wins.
FEATURE_ROUTES: dict[str, list[str]] = {
    "assistant": ["local", "cloud"],
    "workflow": ["cloud", "local"],
    "analytics": ["local", "cloud"],
    "default": ["local", "cloud"],
}

# Demo entitlements. Replace with identity/entitlement services in production.
FEATURE_LICENSES = {
    "assistant": "ai-assistant",
    "workflow": "agentic-workflow",
    "analytics": "ai-analytics",
    "default": "ai-chat",
}

ROLE_FEATURES = {
    "admin": {"assistant", "workflow", "analytics", "default"},
    "operator": {"assistant", "analytics", "default"},
    "developer": {"assistant", "workflow", "analytics", "default"},
}

TOKENS = {
    "demo-admin-token": "admin",
    "demo-operator-token": "operator",
    "demo-developer-token": "developer",
}

TOKEN_BUDGET = 5000
