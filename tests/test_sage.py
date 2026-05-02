import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from premium_agents.sage_daily_brief import SageAgent

_FAKE_BRIEF = {
    "date": "2026-05-01",
    "headline": "Label is on track — three key actions for the week.",
    "priority_actions": [
        {"rank": 1, "action": "Confirm tour routing for Artist A", "context": "Dates window closing", "urgency": "high"},
        {"rank": 2, "action": "Review studio session bookings", "context": "Q2 pipeline", "urgency": "medium"},
        {"rank": 3, "action": "Update release schedule", "context": "Distributor deadline", "urgency": "low"},
    ],
    "flags": [],
    "upcoming_in_7_days": ["Artist A show — venue TBC"],
    "one_win": "Merch sell-through hit 85% last week.",
}


def test_sage_run_with_mock_llm():
    """SAGE agent returns a valid structured brief when the LLM is mocked."""
    agent = SageAgent()
    with patch.object(agent, "llm", return_value=json.dumps(_FAKE_BRIEF)):
        result = agent.run({"scope": "daily"})

    assert result["agent"] == "SAGE", f"Expected agent='SAGE', got {result['agent']!r}"
    assert result["status"] == "complete", (
        f"Expected status='complete', got {result['status']!r}. "
        f"Message: {result.get('message')}"
    )
    data = result["data"]
    assert "headline" in data, "Brief data must contain 'headline'"
    assert "priority_actions" in data, "Brief data must contain 'priority_actions'"
    assert isinstance(data["priority_actions"], list), "'priority_actions' must be a list"
    assert len(data["priority_actions"]) > 0, "'priority_actions' must not be empty"


def test_sage_run_llm_error_raises():
    """SAGE agent returns status='error' (not a silent pass) when the LLM fails."""
    agent = SageAgent()
    with patch.object(agent, "llm", side_effect=RuntimeError("LLM unavailable")):
        result = agent.run({"scope": "daily"})

    assert result["status"] == "error", (
        "SAGE must surface LLM errors as status='error', not silently succeed"
    )
    assert result["agent"] == "SAGE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
