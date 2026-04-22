from job_store import JobStore
import os

# Optionally set REDIS_URL here for testing
# os.environ["REDIS_URL"] = "redis://localhost:6379/0"

store = JobStore()

print("Adding test job...")
store.add_job("test_job_1", {"foo": "bar", "num": 42})

print("Fetching test job...")
job = store.get_job("test_job_1")
print("Fetched job:", job)

print("Listing all jobs...")
all_jobs = store.all_jobs()
print("All jobs:", all_jobs)

print("Deleting test job...")
store.delete_job("test_job_1")
print("Deleted. All jobs now:", store.all_jobs())
