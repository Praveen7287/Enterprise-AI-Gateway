# Enterprise AI Gateway — AI Control Plane Reference Implementation

Reference implementation accompanying the article:

**Designing an Enterprise AI Gateway: From LLM API Wrapper to AI Control Plane**

This project demonstrates how an enterprise AI Gateway can provide one governed entry point for multiple AI consumers and model providers.

## What it demonstrates

- OpenAI-style `/v1/chat/completions` API
- Feature-based model/provider routing
- Provider abstraction
- Authentication
- Role-based feature authorization
- License/entitlement checks
- Token-budget governance
- Provider fallback / graceful degradation
- Metadata-only audit logging
- Stable non-2xx provider failure contract
- Automated regression tests
- Docker packaging

## Architecture

```text
IM HUB / Enterprise App / Workflow / Analytics
                    |
                    | HTTPS + JWT
                    v
        +----------------------------+
        |      Enterprise AI         |
        |          Gateway           |
        +----------------------------+
        | Auth / RBAC / Entitlement  |
        | Feature Routing            |
        | Token & Cost Governance    |
        | Audit / Observability      |
        | Guardrails / Resilience    |
        +-------------+--------------+
                      |
             +--------+--------+
             |                 |
             v                 v
        Local / Ollama     Cloud / BYOK
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the detailed request flow and [`docs/ARTICLE_MAPPING.md`](docs/ARTICLE_MAPPING.md) for the mapping from article concepts to code.

## Project structure

```text
enterprise-ai-gateway/
├── src/
│   ├── gateway/
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── policies.py
│   │   ├── service.py
│   │   └── audit.py
│   └── providers/
│       ├── base.py
│       └── mock.py
├── tests/
│   └── test_gateway.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── ARTICLE_MAPPING.md
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Run locally

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the gateway

```bash
uvicorn gateway.app:app --app-dir src --reload
```

Open Swagger UI at `http://127.0.0.1:8000/docs`.

### 4. Test the API

```bash
curl -X POST "http://127.0.0.1:8000/v1/chat/completions" \
  -H "Authorization: Bearer demo-admin-token" \
  -H "X-AI-Feature: assistant" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Explain what an AI Gateway does."}]}'
```

Expected response shape:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "model": "demo-local",
  "content": "Demo response from local: Explain what an AI Gateway does.",
  "provider": "local",
  "usage": {
    "prompt_tokens": 7,
    "completion_tokens": 9,
    "total_tokens": 16
  },
  "estimated_cost": 0.0,
  "fallback_used": false
}
```

## Feature routing example

`gateway/config.py` contains the reference policy:

```python
FEATURE_ROUTES = {
    "assistant": ["local", "cloud"],
    "workflow": ["cloud", "local"],
    "analytics": ["local", "cloud"],
    "default": ["local", "cloud"],
}
```

This is intentionally simple. A production implementation could route on feature, data classification, latency target, model capability, tenant policy, cost ceiling, region, or provider health.

## Fallback demonstration

The test suite disables the local provider and verifies that the gateway automatically uses the cloud provider:

```text
assistant request
      |
      v
    local  -- unavailable --> cloud
                              |
                              v
                           response
```

## Run tests

```bash
pytest -q
```

## Docker

```bash
docker build -t enterprise-ai-gateway .
docker run --rm -p 8000:8000 enterprise-ai-gateway
```

## Production hardening

This repository is a portfolio/reference implementation, not a production security boundary. Before production use, replace the demo components with:

- OIDC/OAuth2/JWT validation and enterprise identity integration
- Secret manager / KMS-backed provider credentials
- TLS/mTLS where appropriate
- Durable audit/event storage
- Distributed quotas and rate limiting
- Tenant isolation
- Provider health checks and circuit breakers
- OpenTelemetry metrics, logs and traces
- Structured prompt/data classification
- PII and secret redaction
- Request size and abuse controls
- Model allowlists and capability policies
- Key rotation and credential lifecycle management
- Persistent license/entitlement service

## Portfolio-safe scope

The implementation is intentionally generic and uses mock providers, synthetic configuration, and demo credentials. It does **not** contain proprietary company code, customer information, internal URLs, credentials, or confidential implementation details.
