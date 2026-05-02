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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
