import json
import pytest
from unittest.mock import patch
from dashboard.app import app

def _login(client):
    with client.session_transaction() as sess:
        sess["authenticated"] = True

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_focus_brief_returns_json(client):
    _login(client)
    # Patch data sources to ensure deterministic output
    with patch("premium_agents.focus.get_pending_approvals", return_value=[]), \
         patch("builtins.open", create=True), \
         patch("pathlib.Path.exists", return_value=False):
        resp = client.get("/label/api/focus/brief")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "approvals" in data
        assert "missions" in data
        assert "upcoming_shows" in data


def test_focus_brief_handles_error(client):
    _login(client)
    # Simulate error in get_pending_approvals (patch correct import path for dynamic loader)
    with patch("crews.base_crew.get_pending_approvals", side_effect=Exception("fail")):
        resp = client.get("/label/api/focus/brief")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status"] == "error"
        assert "error" in data
