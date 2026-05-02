"""Integration tests for the /agents/run/<agent_name> endpoint."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _login(client):
    with client.session_transaction() as sess:
        sess["authenticated"] = True


class TestAgentRunEndpoint:
    def test_run_unknown_agent_returns_404(self, client):
        _login(client)
        response = client.post("/agents/run/NONEXISTENT_AGENT_XYZ")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_run_requires_login(self, client):
        response = client.post("/agents/run/FocusAgent")
        # Must redirect to login (302) or return 401 — not 200/404 with data
        assert response.status_code in (302, 401)

    def test_run_focus_agent_returns_result(self, client):
        _login(client)
        response = client.post("/agents/run/FocusAgent")
        # FocusAgent should always succeed (no LLM needed)
        assert response.status_code == 200
        data = response.get_json()
        assert "result" in data
        assert data["result"]["status"] == "complete"

    def test_run_ledger_agent_returns_result(self, client):
        _login(client)
        response = client.post("/agents/run/LedgerAgent")
        assert response.status_code == 200
        data = response.get_json()
        assert "result" in data
        assert data["result"]["status"] == "complete"

    def test_run_multi_label_onboarding_returns_result(self, client):
        _login(client)
        response = client.post("/agents/run/MultiLabelOnboardingAgent")
        assert response.status_code == 200
        data = response.get_json()
        assert "result" in data
        assert data["result"]["status"] == "complete"


class TestAgentsListEndpoint:
    def test_agents_list_requires_login(self, client):
        response = client.get("/agents")
        assert response.status_code in (302, 401)

    def test_agents_list_returns_200(self, client):
        _login(client)
        response = client.get("/agents")
        assert response.status_code == 200

    def test_agents_list_contains_premium_links_when_enabled(self, client):
        _login(client)
        with patch("dashboard.app.PREMIUM_FEATURES_ENABLED", True):
            response = client.get("/agents")
        assert response.status_code == 200
        html = response.data.decode()
        assert "/agents/focus" in html
        assert "/agents/multi-label-onboarding" in html


class TestFocusAgentPage:
    def test_focus_page_requires_login(self, client):
        response = client.get("/agents/focus")
        assert response.status_code in (302, 401)

    def test_focus_page_get_returns_200(self, client):
        _login(client)
        response = client.get("/agents/focus")
        assert response.status_code == 200

    def test_focus_page_shows_form_when_premium_enabled(self, client):
        _login(client)
        with patch("dashboard.app.PREMIUM_FEATURES_ENABLED", True):
            response = client.get("/agents/focus")
        assert response.status_code == 200
        html = response.data.decode()
        assert "max_items" in html
        assert "artist_slug" in html

    def test_focus_page_shows_gate_when_premium_disabled(self, client):
        _login(client)
        with patch("dashboard.app.PREMIUM_FEATURES_ENABLED", False):
            response = client.get("/agents/focus")
        assert response.status_code == 200
        html = response.data.decode()
        assert "PREMIUM_FEATURES_ENABLED" in html

    def test_focus_page_post_runs_agent_when_premium_enabled(self, client):
        _login(client)
        with patch("dashboard.app.PREMIUM_FEATURES_ENABLED", True):
            response = client.post("/agents/focus", data={"max_items": "5", "artist_slug": ""})
        assert response.status_code == 200
        html = response.data.decode()
        assert "Priority Queue" in html

    def test_focus_page_post_ignored_when_premium_disabled(self, client):
        _login(client)
        with patch("dashboard.app.PREMIUM_FEATURES_ENABLED", False):
            response = client.post("/agents/focus", data={"max_items": "5"})
        assert response.status_code == 200
        html = response.data.decode()
        assert "PREMIUM_FEATURES_ENABLED" in html


class TestMultiLabelOnboardingPage:
    def test_onboarding_page_requires_login(self, client):
        response = client.get("/agents/multi-label-onboarding")
        assert response.status_code in (302, 401)

    def test_onboarding_page_get_returns_200(self, client):
        _login(client)
        response = client.get("/agents/multi-label-onboarding")
        assert response.status_code == 200

    def test_onboarding_page_shows_form_when_premium_enabled(self, client):
        _login(client)
        with patch("dashboard.app.PREMIUM_FEATURES_ENABLED", True):
            response = client.get("/agents/multi-label-onboarding")
        assert response.status_code == 200
        html = response.data.decode()
        assert "label_name" in html
        assert "owner_name" in html
        assert "genre_focus" in html

    def test_onboarding_page_shows_gate_when_premium_disabled(self, client):
        _login(client)
        with patch("dashboard.app.PREMIUM_FEATURES_ENABLED", False):
            response = client.get("/agents/multi-label-onboarding")
        assert response.status_code == 200
        html = response.data.decode()
        assert "PREMIUM_FEATURES_ENABLED" in html

    def test_onboarding_page_post_runs_agent_when_premium_enabled(self, client):
        _login(client)
        with patch("dashboard.app.PREMIUM_FEATURES_ENABLED", True):
            response = client.post("/agents/multi-label-onboarding", data={
                "label_name": "Test Label",
                "label_slug": "",
                "owner_name": "Jordan Lee",
                "owner_email": "test@example.com",
                "genre_focus": "Indie Pop",
                "artist_count": "3",
                "use_llm": "no",
            })
        assert response.status_code == 200
        html = response.data.decode()
        assert "Onboarding Package" in html
        assert "Test Label" in html

    def test_onboarding_page_post_ignored_when_premium_disabled(self, client):
        _login(client)
        with patch("dashboard.app.PREMIUM_FEATURES_ENABLED", False):
            response = client.post("/agents/multi-label-onboarding", data={
                "label_name": "Test Label",
            })
        assert response.status_code == 200
        html = response.data.decode()
        assert "PREMIUM_FEATURES_ENABLED" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
