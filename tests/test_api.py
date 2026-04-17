import pytest
from dashboard.app import app  # adjust import path if your Flask app is elsewhere

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def _login(client):
    with client.session_transaction() as sess:
        sess["authenticated"] = True


def test_hub_requires_login_redirect(client):
    response = client.get("/hub")
    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")


def test_checkin_requires_login(client):
    response = client.post("/label/api/checkin/aria_velvet", json={"note": "Test check-in"})
    assert response.status_code == 401
    data = response.get_json()
    assert data.get("error") == "Unauthorized"


def test_checkin_ok_when_authenticated(client):
    _login(client)
    response = client.post("/label/api/checkin/aria_velvet", json={"note": "Test check-in"})
    data = response.get_json()
    assert response.status_code == 200
    assert data.get("success") is True
    assert "output" in data


def test_webhook_requires_configured_url(client, monkeypatch):
    monkeypatch.delenv("WEBHOOK_URL", raising=False)
    _login(client)
    response = client.post("/label/api/webhook/aria_velvet")
    data = response.get_json()
    assert response.status_code == 503
    assert data.get("sent") is False
    assert data.get("error") == "WEBHOOK_URL not configured."