"""Tests for the FOCUS premium agent (CEO Priority Queue)."""
import json
import sys
from datetime import date, timedelta, timezone, datetime as dt
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from premium_agents.focus import FocusAgent


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_artist(slug, last_contact_days_ago=5, open_actions=None, tmp_path=None):
    """Write a minimal artist JSON file and return its path."""
    today = dt.now(timezone.utc).date()
    last_contact = (today - timedelta(days=last_contact_days_ago)).isoformat()
    artist = {
        "artist_info": {
            "name": slug.replace("_", " ").title(),
            "slug": slug,
            "last_contact_date": last_contact,
        },
        "open_action_items": open_actions or [],
    }
    path = tmp_path / f"{slug}.json"
    path.write_text(json.dumps(artist))
    return path


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestFocusBasic:
    def test_returns_complete_status(self, tmp_path):
        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = tmp_path / "artists"
        agent.artists_dir.mkdir()
        result = agent.run({})
        assert result["status"] == "complete"
        assert result["agent"] == "FOCUS"

    def test_data_keys_present(self, tmp_path):
        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = tmp_path / "artists"
        agent.artists_dir.mkdir()
        data = agent.run({})["data"]
        assert "priority_queue" in data
        assert "generated_at" in data
        assert "total_items" in data

    def test_empty_roster_returns_empty_queue(self, tmp_path):
        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = tmp_path / "artists"
        agent.artists_dir.mkdir()
        data = agent.run({})["data"]
        assert data["priority_queue"] == []
        assert data["total_items"] == 0


class TestFocusStaleArtists:
    def test_stale_artist_appears_in_queue(self, tmp_path):
        artists_dir = tmp_path / "artists"
        artists_dir.mkdir()
        _make_artist("old_artist", last_contact_days_ago=20, tmp_path=artists_dir)

        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = artists_dir
        data = agent.run({})["data"]

        types = [i["rank_type"] for i in data["priority_queue"]]
        assert "stale_contact" in types

    def test_recent_contact_not_in_queue(self, tmp_path):
        artists_dir = tmp_path / "artists"
        artists_dir.mkdir()
        _make_artist("fresh_artist", last_contact_days_ago=3, tmp_path=artists_dir)

        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = artists_dir
        data = agent.run({})["data"]

        types = [i["rank_type"] for i in data["priority_queue"]]
        assert "stale_contact" not in types


class TestFocusOverdueActions:
    def test_overdue_action_appears_in_queue(self, tmp_path):
        artists_dir = tmp_path / "artists"
        artists_dir.mkdir()
        past_due = (dt.now(timezone.utc).date() - timedelta(days=3)).isoformat()
        overdue_action = {
            "description": "Send press kit",
            "assigned_to": "Label",
            "due_date": past_due,
            "priority": "high",
        }
        _make_artist("busy_artist", last_contact_days_ago=1, open_actions=[overdue_action], tmp_path=artists_dir)

        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = artists_dir
        data = agent.run({})["data"]

        types = [i["rank_type"] for i in data["priority_queue"]]
        assert "overdue_action" in types

    def test_future_due_date_not_in_queue(self, tmp_path):
        artists_dir = tmp_path / "artists"
        artists_dir.mkdir()
        future_due = (dt.now(timezone.utc).date() + timedelta(days=5)).isoformat()
        future_action = {
            "description": "Prepare release assets",
            "assigned_to": "Label",
            "due_date": future_due,
            "priority": "medium",
        }
        _make_artist("future_artist", last_contact_days_ago=1, open_actions=[future_action], tmp_path=artists_dir)

        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = artists_dir
        data = agent.run({})["data"]

        types = [i["rank_type"] for i in data["priority_queue"]]
        assert "overdue_action" not in types


class TestFocusApprovals:
    def test_pending_approvals_appear_in_queue(self, tmp_path):
        fake_pending = [
            {
                "task_id": "VINYL_post_social_media_20260501_120000",
                "action": "post_social_media",
                "agent": "VINYL",
                "payload": {},
                "status": "pending",
                "queued_at": "2026-05-01T12:00:00+00:00",
            }
        ]
        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = tmp_path / "artists"
        agent.artists_dir.mkdir()

        with patch("premium_agents.focus.get_pending_approvals", return_value=fake_pending):
            data = agent.run({})["data"]

        types = [i["rank_type"] for i in data["priority_queue"]]
        assert "approval" in types

    def test_no_approvals_when_queue_empty(self, tmp_path):
        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = tmp_path / "artists"
        agent.artists_dir.mkdir()

        with patch("premium_agents.focus.get_pending_approvals", return_value=[]):
            data = agent.run({})["data"]

        types = [i["rank_type"] for i in data["priority_queue"]]
        assert "approval" not in types


class TestFocusMaxItems:
    def test_max_items_caps_queue(self, tmp_path):
        artists_dir = tmp_path / "artists"
        artists_dir.mkdir()
        # Create 10 stale artists to populate the queue
        for i in range(10):
            _make_artist(f"artist_{i}", last_contact_days_ago=20, tmp_path=artists_dir)

        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = artists_dir
        data = agent.run({"max_items": "5"})["data"]

        assert len(data["priority_queue"]) <= 5


class TestFocusArtistFilter:
    def test_artist_filter_limits_results(self, tmp_path):
        artists_dir = tmp_path / "artists"
        artists_dir.mkdir()
        _make_artist("target_artist", last_contact_days_ago=20, tmp_path=artists_dir)
        _make_artist("other_artist", last_contact_days_ago=20, tmp_path=artists_dir)

        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = artists_dir
        data = agent.run({"artist_slug": "target_artist"})["data"]

        for item in data["priority_queue"]:
            assert item.get("artist_slug") == "target_artist"

    def test_ranks_are_sequential(self, tmp_path):
        artists_dir = tmp_path / "artists"
        artists_dir.mkdir()
        _make_artist("rank_artist", last_contact_days_ago=20, tmp_path=artists_dir)

        agent = FocusAgent(data_root=tmp_path)
        agent.artists_dir = artists_dir
        data = agent.run({})["data"]

        ranks = [i["rank"] for i in data["priority_queue"]]
        assert ranks == list(range(1, len(ranks) + 1))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
