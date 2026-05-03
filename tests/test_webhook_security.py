"""
Webhook secret validation tests for webhook_server.py.
Covers: missing secret, invalid secret, valid secret (X-WEBHOOK-SECRET and Bearer).
All tests use Flask's test client; no external services required.
"""
import os
import pytest
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webhook_server import app as webhook_app


@pytest.fixture
def client():
    webhook_app.config["TESTING"] = True
    with webhook_app.test_client() as c:
        yield c


WEBHOOK_ROUTES = [
    "/webhook/easyfunnels/crm-update",
    "/webhook/easyfunnels/order",
    "/webhook/easyfunnels/appointment",
    "/webhook/maestro-approved-action",
]


class TestWebhookSecretValidation:
    """Webhook routes must reject requests without a valid secret."""

    @pytest.mark.parametrize("route", WEBHOOK_ROUTES)
    def test_no_secret_configured_returns_401(self, client, monkeypatch, route):
        """If WEBHOOK_SECRET is not configured, all requests must be rejected."""
        monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
        resp = client.post(route, json={})
        assert resp.status_code == 401, f"{route} should return 401 when WEBHOOK_SECRET is unset"

    @pytest.mark.parametrize("route", WEBHOOK_ROUTES)
    def test_missing_secret_header_returns_401(self, client, monkeypatch, route):
        """Requests without the secret header must be rejected."""
        monkeypatch.setenv("WEBHOOK_SECRET", "test-secret-abc")
        resp = client.post(route, json={})
        assert resp.status_code == 401, f"{route} should return 401 when secret header is missing"

    @pytest.mark.parametrize("route", WEBHOOK_ROUTES)
    def test_invalid_secret_header_returns_401(self, client, monkeypatch, route):
        """Requests with a wrong X-WEBHOOK-SECRET must be rejected."""
        monkeypatch.setenv("WEBHOOK_SECRET", "test-secret-abc")
        resp = client.post(route, json={}, headers={"X-WEBHOOK-SECRET": "wrong-secret"})
        assert resp.status_code == 401, f"{route} should return 401 with wrong secret"

    @pytest.mark.parametrize("route", WEBHOOK_ROUTES)
    def test_invalid_bearer_token_returns_401(self, client, monkeypatch, route):
        """Requests with a wrong Bearer token must be rejected."""
        monkeypatch.setenv("WEBHOOK_SECRET", "test-secret-abc")
        resp = client.post(route, json={}, headers={"Authorization": "Bearer wrong-token"})
        assert resp.status_code == 401, f"{route} should return 401 with wrong Bearer token"

    @pytest.mark.parametrize("route", WEBHOOK_ROUTES)
    def test_valid_secret_header_accepted(self, client, monkeypatch, route):
        """Requests with correct X-WEBHOOK-SECRET must be accepted (not 401)."""
        monkeypatch.setenv("WEBHOOK_SECRET", "test-secret-abc")
        monkeypatch.setenv("MAESTRO_BASE_URL", "http://localhost:8080")
        monkeypatch.setenv("N8N_BASE_URL", "http://localhost:5678")
        with patch("webhook_server._req.post") as mock_post:
            mock_post.return_value.json.return_value = {}
            resp = client.post(
                route,
                json={"workflow": "noop", "payload": {}},
                headers={"X-WEBHOOK-SECRET": "test-secret-abc"},
            )
        assert resp.status_code != 401, f"{route} should not return 401 with correct secret"
        assert resp.status_code != 403, f"{route} should not return 403 with correct secret"

    @pytest.mark.parametrize("route", WEBHOOK_ROUTES)
    def test_valid_bearer_token_accepted(self, client, monkeypatch, route):
        """Requests with correct Authorization: Bearer token must be accepted (not 401)."""
        monkeypatch.setenv("WEBHOOK_SECRET", "test-secret-abc")
        monkeypatch.setenv("MAESTRO_BASE_URL", "http://localhost:8080")
        monkeypatch.setenv("N8N_BASE_URL", "http://localhost:5678")
        with patch("webhook_server._req.post") as mock_post:
            mock_post.return_value.json.return_value = {}
            resp = client.post(
                route,
                json={"workflow": "noop", "payload": {}},
                headers={"Authorization": "Bearer test-secret-abc"},
            )
        assert resp.status_code != 401, f"{route} should not return 401 with correct Bearer token"
        assert resp.status_code != 403, f"{route} should not return 403 with correct Bearer token"


class TestBearerTokenAuth:
    """Label API routes must accept Bearer token in addition to session auth."""

    def test_mission_list_with_bearer_token(self, monkeypatch):
        """GET /label/api/mission/list accepts X-MAESTRO-TOKEN header."""
        monkeypatch.setenv("MAESTRO_TOKEN", "test-dashboard-token")
        from dashboard.app import app as dashboard_app
        dashboard_app.config["TESTING"] = True
        with dashboard_app.test_client() as c:
            resp = c.get(
                "/label/api/mission/list",
                headers={"X-MAESTRO-TOKEN": "test-dashboard-token"},
            )
        assert resp.status_code == 200

    def test_mission_list_with_wrong_token_returns_401(self, monkeypatch):
        """GET /label/api/mission/list rejects an incorrect X-MAESTRO-TOKEN."""
        monkeypatch.setenv("MAESTRO_TOKEN", "test-dashboard-token")
        from dashboard.app import app as dashboard_app
        dashboard_app.config["TESTING"] = True
        with dashboard_app.test_client() as c:
            resp = c.get(
                "/label/api/mission/list",
                headers={"X-MAESTRO-TOKEN": "wrong-token"},
            )
        assert resp.status_code == 401

    def test_mission_list_with_authorization_bearer(self, monkeypatch):
        """GET /label/api/mission/list accepts Authorization: Bearer <token>."""
        monkeypatch.setenv("MAESTRO_TOKEN", "test-dashboard-token")
        from dashboard.app import app as dashboard_app
        dashboard_app.config["TESTING"] = True
        with dashboard_app.test_client() as c:
            resp = c.get(
                "/label/api/mission/list",
                headers={"Authorization": "Bearer test-dashboard-token"},
            )
        assert resp.status_code == 200
