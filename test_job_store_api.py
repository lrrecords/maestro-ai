import requests
import time

BASE = "http://127.0.0.1:5000/label/api/mission"

# Add your MAESTRO_TOKEN here
TOKEN = "q5mBjUuheDnG8JgqSy842YJCD-8Lc8Z70qkQ-r5gm-M"
headers = {"Authorization": f"Bearer {TOKEN}"}

 # 1. Create a new mission/job
resp = requests.post(BASE, json={
    "artist_slug": "test_artist",
    "mission": "Test persistent job store",
    "release_title": "Test Release"
}, headers=headers)
print("Create mission response:", resp.json())
assert resp.ok and "job_id" in resp.json(), "Failed to create mission"
job_id = resp.json()["job_id"]

 # 2. List all missions/jobs
resp = requests.get(BASE + "/list", headers=headers)
print("Mission list:", resp.json())
assert resp.ok and any(j["job_id"] == job_id for j in resp.json()["jobs"]), "Job not found in list"

 # 3. Poll job status
for _ in range(10):
    resp = requests.get(f"{BASE}/{job_id}", headers=headers)
    data = resp.json()
    print("Job status:", data)
    if data.get("job", {}).get("status") in ("complete", "error", "cancelled"):
        break
    time.sleep(1)
else:
    print("Job did not complete in time.")

 # 4. Cancel the job (should be no-op if already complete)
resp = requests.post(f"{BASE}/{job_id}/cancel", headers=headers)
print("Cancel job response:", resp.json())

 # 5. Delete the job
resp = requests.delete(f"{BASE}/{job_id}", headers=headers)
print("Delete job response:", resp.json())
assert resp.ok and resp.json().get("cleared"), "Job not deleted"

 # 6. Confirm deletion
resp = requests.get(BASE + "/list", headers=headers)
print("Mission list after delete:", resp.json())
assert job_id not in [j["job_id"] for j in resp.json()["jobs"]], "Job still present after delete"

print("All job store API tests passed.")
