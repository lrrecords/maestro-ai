# crews/base_crew.py
"""
CEO approval queue — all protected actions must pass through here.
Protected actions: mass email, public posts, money spend, NFT mint, bulk CRM updates.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

APPROVAL_QUEUE_PATH = Path("data/ceo_approval_queue.json")

# Tasks that ALWAYS require CEO sign-off before execution
PROTECTED_ACTIONS = {
    "send_mass_email",
    "publish_public_content",
    "spend_money",
    "bulk_crm_update",
    "mint_nft",
    "post_social_media",
    "sign_contract",
    "orchard_submission",
    "spotify_playlist_pitch",
    "press_outreach",
}


def requires_approval(action_type: str) -> bool:
    return action_type in PROTECTED_ACTIONS


def queue_for_approval(action_type: str, payload: dict, agent_name: str) -> str:
    """Add a task to the CEO approval queue. Returns task_id."""
    queue = _load_queue()
    ts = datetime.now(timezone.utc).isoformat()
    task_id = f"{agent_name}_{action_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    queue.append({
        "task_id":   task_id,
        "action":    action_type,
        "agent":     agent_name,
        "payload":   payload,
        "status":    "pending",
        "queued_at": ts,
    })
    _save_queue(queue)
    return task_id


def approve_task(task_id: str, approved: bool, note: str = "") -> dict:
    queue = _load_queue()
    for item in queue:
        if item["task_id"] == task_id:
            item["status"]     = "approved" if approved else "rejected"
            item["ceo_note"]   = note
            item["actioned_at"] = datetime.now(timezone.utc).isoformat()
            _save_queue(queue)
            return item
    return {"error": "Task not found"}


def get_pending_approvals() -> list:
    return [t for t in _load_queue() if t["status"] == "pending"]


def get_all_approvals(limit: int = 50) -> list:
    return _load_queue()[-limit:]


def _load_queue() -> list:
    if APPROVAL_QUEUE_PATH.exists():
        try:
            return json.loads(APPROVAL_QUEUE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_queue(queue: list):
    APPROVAL_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    APPROVAL_QUEUE_PATH.write_text(
        json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8"
    )
