import json
from pathlib import Path
from typing import Optional, Dict, Any, List

MISSIONS_DIR = Path("data/missions")


def _path(job_id: str) -> Path:
    MISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return MISSIONS_DIR / f"{job_id}.json"


def save_job(job: Dict[str, Any]) -> None:
    job_id = job.get("job_id")
    if not job_id:
        raise ValueError("job missing job_id")
    p = _path(job_id)
    p.write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")


def load_job(job_id: str) -> Optional[Dict[str, Any]]:
    p = _path(job_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def delete_job(job_id: str) -> bool:
    p = _path(job_id)
    if not p.exists():
        return False
    p.unlink()
    return True


def list_jobs(limit: int = 200) -> List[Dict[str, Any]]:
    if not MISSIONS_DIR.exists():
        return []
    jobs: List[Dict[str, Any]] = []
    for p in MISSIONS_DIR.glob("mission_*.json"):
        try:
            jobs.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue

    # Newest first (created_at ISO string sorts lexicographically)
    jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return jobs[:limit]


def patch_job(job_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    job = load_job(job_id)
    if not job:
        return None
    job.update(patch)
    save_job(job)
    return job