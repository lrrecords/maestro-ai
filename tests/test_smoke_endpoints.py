"""
Smoke tests for all major API endpoints and UI flows.
Covers: login, logout, hub, label APIs, missions, approvals, artist CRUD.
All tests use Flask's test client; no external services required.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from dashboard.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _login(client):
    with client.session_transaction() as sess:
        sess["authenticated"] = True


# ---------------------------------------------------------------------------
# Auth flows
# ---------------------------------------------------------------------------

class TestLoginFlow:
    def test_login_page_returns_200(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_login_page_has_form(self, client):
        resp = client.get("/login")
        html = resp.data.decode()
        assert "token" in html.lower()

    def test_login_post_invalid_token_returns_error(self, client):
        with patch("dashboard.app.MAESTRO_TOKEN", "correct-token"):
            resp = client.post("/login", data={"token": "wrong-token"})
        assert resp.status_code == 200
        assert b"Invalid" in resp.data

    def test_login_post_correct_token_redirects(self, client, monkeypatch):
        monkeypatch.setenv("MAESTRO_TOKEN", "correct-token")
        # Re-read the token from env by reloading the module state
        with patch("dashboard.app.MAESTRO_TOKEN", "correct-token"):
            resp = client.post("/login", data={"token": "correct-token"})
        assert resp.status_code == 302

    def test_logout_clears_session_and_redirects(self, client):
        _login(client)
        resp = client.get("/logout")
        assert resp.status_code == 302
        assert "/login" in resp.headers.get("Location", "")
        # Confirm session is cleared
        with client.session_transaction() as sess:
            assert not sess.get("authenticated")


class TestRootAndHub:
    def test_root_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/")
        assert resp.status_code == 302
        assert "/login" in resp.headers.get("Location", "")

    def test_root_authenticated_redirects_to_hub(self, client):
        _login(client)
        resp = client.get("/")
        assert resp.status_code == 302
        assert "/hub" in resp.headers.get("Location", "")

    def test_hub_authenticated_returns_200(self, client):
        _login(client)
        resp = client.get("/hub")
        assert resp.status_code == 200

    def test_hub_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/hub")
        assert resp.status_code == 302
        assert "/login" in resp.headers.get("Location", "")


# ---------------------------------------------------------------------------
# Label API — session / dashboard / artist
# ---------------------------------------------------------------------------

class TestLabelAPISession:
    def test_session_returns_role_and_permissions(self, client):
        _login(client)
        resp = client.get("/label/api/session")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert "role" in data
        assert "permissions" in data

    def test_session_unauthenticated_returns_401(self, client):
        resp = client.get("/label/api/session")
        assert resp.status_code == 401


class TestLabelAPIDashboard:
    def test_dashboard_returns_200_and_list(self, client):
        _login(client)
        resp = client.get("/label/api/dashboard")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_dashboard_unauthenticated_returns_401(self, client):
        resp = client.get("/label/api/dashboard")
        assert resp.status_code == 401


class TestLabelAPIArtist:
    def test_existing_artist_returns_profile(self, client):
        _login(client)
        resp = client.get("/label/api/artist/aria_velvet")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "profile" in data
        assert "score" in data

    def test_missing_artist_returns_404(self, client):
        _login(client)
        resp = client.get("/label/api/artist/nonexistent_slug_xyz")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data

    def test_artist_unauthenticated_returns_401(self, client):
        resp = client.get("/label/api/artist/aria_velvet")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Label API — check-in & webhook
# ---------------------------------------------------------------------------

class TestCheckIn:
    def test_checkin_undefined_slug_returns_400(self, client):
        _login(client)
        resp = client.post("/label/api/checkin/undefined", json={"note": "test"})
        assert resp.status_code == 400

    def test_checkin_valid_slug_returns_success(self, client):
        _login(client)
        resp = client.post("/label/api/checkin/aria_velvet", json={"note": "test"})
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_checkin_unauthenticated_returns_401(self, client):
        resp = client.post("/label/api/checkin/aria_velvet", json={})
        assert resp.status_code == 401


class TestWebhook:
    def test_webhook_undefined_slug_returns_400(self, client, monkeypatch):
        monkeypatch.setenv("WEBHOOK_URL", "http://example.com/hook")
        _login(client)
        resp = client.post("/label/api/webhook/undefined")
        assert resp.status_code == 400

    def test_webhook_no_url_configured_returns_503(self, client, monkeypatch):
        monkeypatch.delenv("WEBHOOK_URL", raising=False)
        _login(client)
        resp = client.post("/label/api/webhook/aria_velvet")
        assert resp.status_code == 503
        assert resp.get_json()["sent"] is False

    def test_webhook_unauthenticated_returns_401(self, client):
        resp = client.post("/label/api/webhook/aria_velvet")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Missions API
# ---------------------------------------------------------------------------

class TestMissionsAPI:
    def test_mission_list_returns_200(self, client):
        _login(client)
        resp = client.get("/label/api/mission/list")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert "jobs" in data

    def test_mission_list_unauthenticated_returns_401(self, client):
        resp = client.get("/label/api/mission/list")
        assert resp.status_code == 401

    def test_mission_create_missing_slug_returns_400(self, client):
        _login(client)
        resp = client.post("/label/api/mission", json={})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_mission_status_missing_job_returns_404(self, client):
        _login(client)
        resp = client.get("/label/api/mission/nonexistent-job-id-xyz")
        assert resp.status_code == 404

    def test_mission_cancel_missing_job_returns_404(self, client):
        _login(client)
        resp = client.post("/label/api/mission/nonexistent-job-id-xyz/cancel")
        assert resp.status_code == 404

    def test_mission_delete_missing_job_returns_404(self, client):
        _login(client)
        resp = client.delete("/label/api/mission/nonexistent-job-id-xyz")
        assert resp.status_code == 404

    def test_mission_create_with_slug_queues_job(self, client):
        _login(client)
        # Patch crew so no real CrewAI call happens
        with patch("label.web.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock(start=MagicMock())
            resp = client.post("/label/api/mission", json={
                "artist_slug": "aria_velvet",
                "mission": "Test smoke mission",
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert "job_id" in data
        assert data["status"] == "running"


# ---------------------------------------------------------------------------
# CEO Approval Queue
# ---------------------------------------------------------------------------

class TestApprovalQueue:
    def test_approval_queue_returns_200(self, client):
        _login(client)
        resp = client.get("/label/api/ceo/queue")
        assert resp.status_code == 200

    def test_approval_queue_unauthenticated_returns_401(self, client):
        resp = client.get("/label/api/ceo/queue")
        assert resp.status_code == 401
