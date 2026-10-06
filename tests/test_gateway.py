import pytest
from fastapi.testclient import TestClient

from gateway.app import app, policy, providers
from providers.mock import MockProvider


client = TestClient(app)


def setup_function():
    policy._reserved = 0
    app.state_test_marker = True
    providers["local"] = MockProvider("local", available=True)
    providers["cloud"] = MockProvider("cloud", available=True)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_completion_routes_and_returns_usage():
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer demo-admin-token", "X-AI-Feature": "assistant"},
        json={"messages": [{"role": "user", "content": "Hello gateway"}]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local"
    assert body["usage"]["total_tokens"] > 0
    assert body["fallback_used"] is False


def test_invalid_credentials_are_rejected():
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer wrong-token"},
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 401


def test_rbac_rejects_operator_workflow_access():
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer demo-operator-token", "X-AI-Feature": "workflow"},
        json={"messages": [{"role": "user", "content": "Run workflow"}]},
    )
    assert response.status_code == 403


def test_fallback_to_cloud_when_local_is_unavailable():
    providers["local"] = MockProvider("local", available=False)
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer demo-admin-token", "X-AI-Feature": "assistant"},
        json={"messages": [{"role": "user", "content": "Use fallback"}]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "cloud"
    assert body["fallback_used"] is True


def test_provider_failure_returns_502(monkeypatch):
    providers["local"] = MockProvider("local", available=False)
    providers["cloud"] = MockProvider("cloud", available=False)
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer demo-admin-token", "X-AI-Feature": "assistant"},
        json={"messages": [{"role": "user", "content": "No providers"}]},
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "No AI provider is currently available"


def test_audit_endpoint_requires_admin():
    response = client.get(
        "/admin/audit",
        headers={"Authorization": "Bearer demo-operator-token"},
    )
    assert response.status_code == 403


def test_audit_endpoint_is_available_to_admin():
    response = client.get(
        "/admin/audit",
        headers={"Authorization": "Bearer demo-admin-token"},
    )
    assert response.status_code == 200
    assert "events" in response.json()
