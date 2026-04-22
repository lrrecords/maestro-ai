import pytest
from dashboard.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def _login(client, role=None, permissions=None):
    with client.session_transaction() as sess:
        sess["authenticated"] = True
        if role:
            sess["role"] = role
        # Optionally, you could add permissions to session if your backend supports it

def test_api_session_ceo(client):
    _login(client, role="ceo")
    resp = client.get("/label/api/session")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["role"] == "ceo"
    assert "can_approve" in data["permissions"]
    assert data["ok"] is True

def test_api_session_user(client):
    _login(client, role="user")
    resp = client.get("/label/api/session")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["role"] == "user"
    assert "can_approve" not in data["permissions"]
    assert data["ok"] is True

def test_api_session_admin(client):
    _login(client, role="admin")
    resp = client.get("/label/api/session")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["role"] == "admin"
    assert "can_approve" in data["permissions"]
    assert "can_edit" in data["permissions"]
    assert data["ok"] is True

def test_api_session_unauthenticated(client):
    resp = client.get("/label/api/session")
    assert resp.status_code in (401, 302)  # Depending on your auth logic
