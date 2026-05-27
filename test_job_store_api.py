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

def test_job_store_lifecycle(client):
    _login(client)
    # Patch crew so no real CrewAI call happens
    with patch("label.web.threading.Thread") as mock_thread:
        mock_thread.return_value = MagicMock(start=MagicMock())
        # 1. Create a new mission/job
        resp = client.post("/label/api/mission", json={
            "artist_slug": "test_artist",
            "mission": "Test persistent job store",
            "release_title": "Test Release"
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True and "job_id" in data, "Failed to create mission"
        job_id = data["job_id"]

    # 2. List all missions/jobs
    resp = client.get("/label/api/mission/list")
    assert resp.status_code == 200
    jobs = resp.get_json()["jobs"]
    assert any(j["job_id"] == job_id for j in jobs), "Job not found in list"

    # 3. Get job status
    resp = client.get(f"/label/api/mission/{job_id}")
    assert resp.status_code == 200
    job = resp.get_json().get("job", {})
    assert job.get("job_id") == job_id

    # 4. Cancel the job (should be no-op if already complete)
    resp = client.post(f"/label/api/mission/{job_id}/cancel")
    assert resp.status_code in (200, 400, 404)

    # 5. Delete the job
    resp = client.delete(f"/label/api/mission/{job_id}")
    assert resp.status_code == 200
    assert resp.get_json().get("cleared"), "Job not deleted"

    # 6. Confirm deletion
    resp = client.get("/label/api/mission/list")
    jobs = resp.get_json()["jobs"]
    assert job_id not in [j["job_id"] for j in jobs], "Job still present after delete"
