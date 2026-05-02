from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.base_agent import BaseAgent
from crews.base_crew import get_pending_approvals


class FocusAgent(BaseAgent):
    """CEO Priority Queue Agent — surfaces pending approvals, overdue tasks, and
    active missions so the label CEO can act on the highest-priority items first."""

    name = "FOCUS"
    department = "premium"
    description = "CEO Priority Queue: pending approvals, overdue tasks, and top missions."

    FIELDS = [
        {
            "key": "max_items",
            "label": "Max Priority Items",
            "type": "select",
            "options": ["5", "10", "20"],
            "default": "10",
        },
        {
            "key": "artist_slug",
            "label": "Filter by Artist (optional)",
            "type": "text",
            "placeholder": "e.g. aria_velvet",
        },
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_dir = Path(__file__).parent.parent
        self.artists_dir = self.root_dir / "data" / "artists"

    def run(self, context: dict) -> dict:
        max_items = int(context.get("max_items", 10))
        artist_slug = context.get("artist_slug")

        priority_items: list[dict] = []

        # 1. Pending CEO approvals (highest priority)
        try:
            pending = get_pending_approvals()
        except Exception:
            pending = []

        for item in pending:
            if artist_slug:
                payload = item.get("payload", {})
                if payload.get("artist_slug") != artist_slug and payload.get("artist") != artist_slug:
                    continue
            priority_items.append({
                "rank_type": "approval",
                "urgency": "high",
                "title": f"Approve: {item.get('action', 'unknown')} [{item.get('agent', '')}]",
                "detail": f"Queued {item.get('queued_at', 'unknown')}. Agent: {item.get('agent')}.",
                "task_id": item.get("task_id"),
            })

        # 2. Overdue open action items across artists
        overdue_items = self._collect_overdue_actions(artist_slug)
        priority_items.extend(overdue_items)

        # 3. Artists with stale contact (no interaction in 14+ days)
        stale_artists = self._collect_stale_artists(artist_slug)
        priority_items.extend(stale_artists)

        # Sort: approvals first, then overdue, then stale; cap at max_items
        priority_items = priority_items[:max_items]

        # Assign rank numbers
        for i, item in enumerate(priority_items, start=1):
            item["rank"] = i

        result_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_items": len(priority_items),
            "priority_queue": priority_items,
            "artist_filter": artist_slug or "all",
        }

        saved_path = self.save_output(result_data, slug="priority_queue")

        return {
            "agent": self.name,
            "department": self.department,
            "status": "complete",
            "message": f"FOCUS queue generated: {len(priority_items)} item(s) require your attention.",
            "data": result_data,
            "saved_to": saved_path,
            "context": context,
        }

    def _collect_overdue_actions(self, artist_slug: str | None) -> list[dict]:
        items = []
        today = datetime.now(timezone.utc).date()
        if not self.artists_dir.exists():
            return items
        for path in sorted(self.artists_dir.glob("*.json")):
            try:
                artist = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            slug = artist.get("artist_info", {}).get("slug", path.stem)
            if artist_slug and slug != artist_slug:
                continue
            name = artist.get("artist_info", {}).get("name", slug)
            for action in artist.get("open_action_items", []):
                due_raw = action.get("due_date")
                if not due_raw:
                    continue
                try:
                    due = datetime.fromisoformat(due_raw).date()
                except ValueError:
                    continue
                if due < today:
                    items.append({
                        "rank_type": "overdue_action",
                        "urgency": "high" if action.get("priority") == "high" else "medium",
                        "title": f"Overdue: {action.get('description', 'Action item')} [{name}]",
                        "detail": (
                            f"Assigned to {action.get('assigned_to', 'unknown')}. "
                            f"Due {due_raw} ({(today - due).days} day(s) overdue)."
                        ),
                        "artist_slug": slug,
                    })
        return items

    def _collect_stale_artists(self, artist_slug: str | None) -> list[dict]:
        items = []
        today = datetime.now(timezone.utc).date()
        if not self.artists_dir.exists():
            return items
        for path in sorted(self.artists_dir.glob("*.json")):
            try:
                artist = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            info = artist.get("artist_info", {})
            slug = info.get("slug", path.stem)
            if artist_slug and slug != artist_slug:
                continue
            name = info.get("name", slug)
            last_contact_raw = info.get("last_contact_date") or info.get("last_interaction")
            if not last_contact_raw:
                continue
            try:
                last = datetime.fromisoformat(last_contact_raw).date()
            except ValueError:
                continue
            days_since = (today - last).days
            if days_since >= 14:
                items.append({
                    "rank_type": "stale_contact",
                    "urgency": "high" if days_since >= 30 else "medium",
                    "title": f"Check in with {name}",
                    "detail": f"Last contact was {days_since} day(s) ago ({last_contact_raw}).",
                    "artist_slug": slug,
                })
        return items
