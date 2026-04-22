
"""
Persistent mission/job store for Maestro AI
- Uses Redis for persistence if available, falls back to in-memory for dev/test
"""


import json
import os

try:
    import redis
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    _redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    _redis.ping()

    USE_REDIS = True
    print("[JobStore] Using Redis for job store")
except Exception:
    _redis = None
    USE_REDIS = False
    print("[JobStore] Using in-memory job store (Redis unavailable)")

class JobStore:
    def __init__(self):
        self._jobs = {}  # fallback in-memory

    def add_job(self, job_id, job_data):
        if USE_REDIS:
            _redis.set(f"maestro:job:{job_id}", json.dumps(job_data))
            _redis.sadd("maestro:jobs", job_id)
        else:
            self._jobs[job_id] = job_data

    def get_job(self, job_id):
        if USE_REDIS:
            data = _redis.get(f"maestro:job:{job_id}")
            if data:
                return json.loads(data)
            return None
        return self._jobs.get(job_id)

    def all_jobs(self):
        if USE_REDIS:
            job_ids = list(_redis.smembers("maestro:jobs"))
            jobs = []
            for job_id in job_ids:
                data = _redis.get(f"maestro:job:{job_id}")
                if data:
                    jobs.append(json.loads(data))
            return jobs
        return list(self._jobs.values())

    def delete_job(self, job_id):
        if USE_REDIS:
            _redis.delete(f"maestro:job:{job_id}")
            _redis.srem("maestro:jobs", job_id)
        else:
            self._jobs.pop(job_id, None)

# Usage example (replace in-memory tracker in mission execution):
# from core.job_store import JobStore
# job_store = JobStore()
# job_store.add_job(...)

# Usage example (replace in-memory tracker in mission execution):
# from core.job_store import JobStore
# job_store = JobStore()
# job_store.add_job(...)
