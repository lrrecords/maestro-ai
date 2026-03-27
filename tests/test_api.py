import pytest
from dashboard.app import app  # adjust import path if your Flask app is elsewhere

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_checkin_ok(client):
    response = client.post("/label/api/checkin/aria_velvet", json={"note": "Test check-in"})
    data = response.get_json()
    assert response.status_code == 200
    assert data.get("success") == True
    assert "output" in data

def test_checkin_undefined(client):
    response = client.post("/label/api/checkin/undefined", json={"note": "Should fail"})
    data = response.get_json()
    assert response.status_code == 400
    assert data.get("success") == False

def test_webhook_ok(client, monkeypatch):
    def mock_post(url, json, timeout):
        class R: status_code = 200
        return R()
    import requests
    monkeypatch.setattr(requests, "post", mock_post)

    response = client.post("/label/api/webhook/aria_velvet")
    data = response.get_json()
    assert response.status_code == 200
    assert data.get("sent") == True

def test_webhook_undefined(client):
    response = client.post("/label/api/webhook/undefined")
    data = response.get_json()
    assert response.status_code == 400
    assert data.get("sent") == False