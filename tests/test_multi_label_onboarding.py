"""Tests for the MultiLabelOnboardingAgent premium agent."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from premium_agents.multi_label_onboarding import MultiLabelOnboardingAgent


class TestMultiLabelOnboardingBasic:
    def test_returns_complete_status(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        result = agent.run({"label_name": "Test Label", "label_slug": "test_label"})
        assert result["status"] == "complete"
        assert result["agent"] == "MULTI_LABEL_ONBOARDING"

    def test_data_keys_present(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data = agent.run({"label_name": "Test Label"})["data"]
        assert "label_name" in data
        assert "onboarding_checklist" in data
        assert "welcome_message" in data
        assert "checklist_total" in data
        assert "generated_at" in data

    def test_checklist_is_populated(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data = agent.run({"label_name": "Test Label"})["data"]
        assert isinstance(data["onboarding_checklist"], list)
        assert len(data["onboarding_checklist"]) > 0

    def test_all_checklist_steps_pending(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data = agent.run({})["data"]
        for step in data["onboarding_checklist"]:
            assert step["status"] == "pending"

    def test_checklist_has_required_keys(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data = agent.run({})["data"]
        for step in data["onboarding_checklist"]:
            assert "step" in step
            assert "task" in step
            assert "category" in step


class TestMultiLabelOnboardingContext:
    def test_label_name_reflected_in_output(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data = agent.run({"label_name": "Galaxy Sound"})["data"]
        assert data["label_name"] == "Galaxy Sound"

    def test_slug_auto_generated_from_name(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data = agent.run({"label_name": "Neon Horizon Records"})["data"]
        assert data["label_slug"] == "neon_horizon_records"

    def test_explicit_slug_is_used(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data = agent.run({"label_name": "X", "label_slug": "custom_slug"})["data"]
        assert data["label_slug"] == "custom_slug"

    def test_owner_details_reflected(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data = agent.run({"label_name": "L", "owner_name": "Alice", "owner_email": "alice@test.com"})["data"]
        assert data["owner_name"] == "Alice"
        assert data["owner_email"] == "alice@test.com"

    def test_welcome_message_contains_owner_name(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data = agent.run({"label_name": "My Label", "owner_name": "Jordan"})["data"]
        assert "Jordan" in data["welcome_message"]

    def test_checklist_total_matches_list_length(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data = agent.run({})["data"]
        assert data["checklist_total"] == len(data["onboarding_checklist"])

    def test_each_run_has_independent_checklist(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        data1 = agent.run({"label_name": "Label A"})["data"]
        data2 = agent.run({"label_name": "Label B"})["data"]
        # Mutating one result must not affect the other
        data1["onboarding_checklist"][0]["status"] = "done"
        assert data2["onboarding_checklist"][0]["status"] == "pending"


class TestMultiLabelOnboardingLLM:
    def test_use_llm_yes_calls_llm(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        with patch.object(agent, "llm", return_value="Welcome aboard, Test Label!") as mock_llm:
            data = agent.run({"label_name": "Test Label", "use_llm": "yes"})["data"]
        mock_llm.assert_called_once()
        assert data["welcome_message"] == "Welcome aboard, Test Label!"

    def test_use_llm_no_skips_llm(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        with patch.object(agent, "llm") as mock_llm:
            agent.run({"label_name": "Test Label", "use_llm": "no"})
        mock_llm.assert_not_called()

    def test_llm_error_falls_back_gracefully(self, tmp_path):
        agent = MultiLabelOnboardingAgent(data_root=tmp_path)
        with patch.object(agent, "llm", side_effect=RuntimeError("LLM unavailable")):
            result = agent.run({"label_name": "Test Label", "use_llm": "yes"})
        assert result["status"] == "complete"
        assert "AI personalisation unavailable" in result["data"]["welcome_message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
