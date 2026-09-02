import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.base_agent import BaseAgent
from live.agents.book import BookAgent
from live.agents.settle import SettleAgent


class DummyAgent(BaseAgent):
    def run(self, context: dict) -> dict:
        return context


def test_call_llm_json_returns_valid_response_without_retry(tmp_path):
    agent = DummyAgent(data_root=tmp_path)
    payload = json.dumps({"alpha": 1, "beta": 2})

    with patch.object(agent, "llm", return_value=payload) as mock_llm:
        result = agent.call_llm_json("Return JSON", required_keys=["alpha", "beta"])

    assert result == {"alpha": 1, "beta": 2}
    assert mock_llm.call_count == 1


def test_call_llm_json_retries_once_when_required_key_is_missing(tmp_path):
    agent = DummyAgent(data_root=tmp_path)
    first = json.dumps({"alpha": 1})
    second = json.dumps({"alpha": 1, "beta": 2})

    with patch.object(agent, "llm", side_effect=[first, second]) as mock_llm:
        result = agent.call_llm_json("Return JSON", required_keys=["alpha", "beta"])

    assert result == {"alpha": 1, "beta": 2}
    assert mock_llm.call_count == 2
    assert "Return valid JSON with ALL of these keys" in mock_llm.call_args_list[1].args[0]


def test_settle_run_returns_error_after_retry_still_missing_keys(tmp_path):
    agent = SettleAgent(data_root=tmp_path)
    context = {
        "gross_box_office": 10000,
        "deal_memo": "70/30 split after expenses",
        "expenses": 1000,
        "currency": "GBP",
    }
    invalid = json.dumps(
        {
            "gross_box_office": 10000,
            "deductible_expenses": 1000,
            "net_box_office": 9000,
            "deal_summary": "70/30 split after expenses",
            "artist_share": 6300,
            "promoter_share": 2700,
        }
    )

    with patch.object(agent, "llm", side_effect=[invalid, invalid]) as mock_llm:
        result = agent.run(context)

    assert result["status"] == "error"
    assert "missing required keys" in result["message"]
    assert mock_llm.call_count == 2


def test_book_run_uses_existing_fallback_after_retry_still_missing_keys(tmp_path):
    agent = BookAgent(data_root=tmp_path)
    context = {
        "artist": "Bicep",
        "dates": ["2026-04-02"],
        "capacity": 1800,
        "territory": "UK",
        "deal_type": "versus",
        "notes": "Prioritize London.",
    }
    invalid = json.dumps(
        {
            "recommendations": ["Confirm avails with top venues."],
            "next_actions": ["Send holds for the requested date."],
        }
    )

    with patch.object(agent, "llm", side_effect=[invalid, invalid]) as mock_llm:
        result = agent.run(context)

    assert result["status"] == "ok"
    assert result["result"]["next_actions"] == []
    assert result["result"]["recommendations"][0] == (
        "Double-check availability for all requested dates before sending holds."
    )
    assert "missing required keys" in result["result"]["risks"][0]
    assert mock_llm.call_count == 2
