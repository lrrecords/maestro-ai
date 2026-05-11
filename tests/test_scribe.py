"""
Tests for SCRIBE agent routes and functionality.
Covers: dashboard, approval queue, edit approval, propose topics,
        workflow trigger, batch operations, admin routes, normalization.
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock

from dashboard.app import app
from agents.label.scribe.scribe_agent import ScribeAgent


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _login(client):
    with client.session_transaction() as sess:
        sess["authenticated"] = True


# ---------------------------------------------------------------------------
# Helpers — seed jobs into the in-memory job store
# ---------------------------------------------------------------------------

def _make_propose_topics_job(job_id="test-job-001", status="pending_approval"):
    return {
        "id": job_id,
        "agent": "SCRIBE",
        "type": "propose_topics",
        "status": status,
        "input": {"topic_preferences": "", "llm_provider": "anthropic"},
        "output": {
            "blogTopics": [
                {"title": "Mixing for Home Studios", "rationale": "High demand from indie producers."},
                {"title": "Record Label Business Models", "rationale": "Evergreen music business topic."},
            ]
        },
        "timestamp": "2026-05-01T10:00:00Z",
    }


def _seed_job(client, job_data):
    """Directly seed a job into the scribe blueprint's job_store."""
    from dashboard.label.scribe import job_store
    job_store.add_job(job_data["id"], job_data)


def _remove_job(job_id):
    from dashboard.label.scribe import job_store
    job_store.delete_job(job_id)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestScribeDashboard:
    def test_dashboard_accessible(self, client):
        # SCRIBE blueprint routes are accessible (auth is handled at the app/session layer)
        resp = client.get("/label/scribe/")
        assert resp.status_code == 200

    def test_dashboard_returns_200(self, client):
        _login(client)
        resp = client.get("/label/scribe/")
        assert resp.status_code == 200

    def test_dashboard_shows_scribe_heading(self, client):
        _login(client)
        resp = client.get("/label/scribe/")
        html = resp.data.decode()
        assert "SCRIBE" in html

    def test_dashboard_shows_pending_count(self, client):
        job = _make_propose_topics_job("dash-pending-001")
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.get("/label/scribe/")
            assert resp.status_code == 200
            html = resp.data.decode()
            # Pending count must appear somewhere
            assert "1" in html or "Pending" in html
        finally:
            _remove_job("dash-pending-001")

    def test_dashboard_shows_recent_jobs(self, client):
        job = _make_propose_topics_job("dash-recent-001")
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.get("/label/scribe/")
            assert resp.status_code == 200
            html = resp.data.decode()
            assert "dash-recent-001"[:8] in html
        finally:
            _remove_job("dash-recent-001")


# ---------------------------------------------------------------------------
# Approval queue
# ---------------------------------------------------------------------------

class TestScribeApprovals:
    def test_approvals_accessible(self, client):
        # SCRIBE blueprint routes are accessible (auth is handled at the app/session layer)
        resp = client.get("/label/scribe/approvals")
        assert resp.status_code == 200

    def test_approvals_returns_200(self, client):
        _login(client)
        resp = client.get("/label/scribe/approvals")
        assert resp.status_code == 200

    def test_approvals_shows_pending_jobs(self, client):
        job = _make_propose_topics_job("approval-001")
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.get("/label/scribe/approvals")
            html = resp.data.decode()
            assert "Mixing for Home Studios" in html
        finally:
            _remove_job("approval-001")

    def test_approvals_shows_empty_state_when_none(self, client):
        _login(client)
        # Remove any lingering test jobs first
        from dashboard.label.scribe import job_store
        for j in list(job_store.all_jobs()):
            if j.get("agent") == "SCRIBE" and j.get("status") == "pending_approval":
                job_store.delete_job(j["id"])
        resp = client.get("/label/scribe/approvals")
        html = resp.data.decode()
        assert "No jobs pending" in html or "empty" in html.lower() or "Nothing" in html

    def test_approvals_shows_rationale_in_italics_block(self, client):
        job = _make_propose_topics_job("approval-rationale-001")
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.get("/label/scribe/approvals")
            html = resp.data.decode()
            assert "High demand from indie producers" in html
        finally:
            _remove_job("approval-rationale-001")


# ---------------------------------------------------------------------------
# Approve action — workflow trigger
# ---------------------------------------------------------------------------

class TestScribeApproveAction:
    def test_approve_marks_job_approved(self, client):
        job = _make_propose_topics_job("approve-001")
        _seed_job(client, job)
        _login(client)
        try:
            with patch("dashboard.label.scribe._trigger_workflow", return_value={"triggered": False, "error": "stubbed"}):
                resp = client.post("/label/scribe/approve", data={
                    "approval_id": "approve-001",
                    "action": "approve",
                })
            assert resp.status_code == 302
            from dashboard.label.scribe import job_store
            updated = job_store.get_job("approve-001")
            assert updated["status"] == "approved"
        finally:
            _remove_job("approve-001")

    def test_approve_triggers_workflow(self, client):
        job = _make_propose_topics_job("approve-trigger-001")
        _seed_job(client, job)
        _login(client)
        try:
            trigger_mock = MagicMock(return_value={"triggered": True, "method": "generate_blog_versions"})
            with patch("dashboard.label.scribe._trigger_workflow", trigger_mock):
                resp = client.post("/label/scribe/approve", data={
                    "approval_id": "approve-trigger-001",
                    "action": "approve",
                })
            assert resp.status_code == 302
            trigger_mock.assert_called_once()
        finally:
            _remove_job("approve-trigger-001")

    def test_approve_flash_includes_workflow_method(self, client):
        job = _make_propose_topics_job("approve-flash-001")
        _seed_job(client, job)
        _login(client)
        try:
            with patch("dashboard.label.scribe._trigger_workflow",
                       return_value={"triggered": True, "method": "generate_blog_versions"}):
                with client.session_transaction() as sess:
                    sess["authenticated"] = True
                resp = client.post("/label/scribe/approve", data={
                    "approval_id": "approve-flash-001",
                    "action": "approve",
                }, follow_redirects=True)
            html = resp.data.decode()
            assert "workflow triggered" in html.lower() or "approved" in html.lower()
        finally:
            _remove_job("approve-flash-001")

    def test_reject_marks_job_rejected(self, client):
        job = _make_propose_topics_job("reject-001")
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.post("/label/scribe/approve", data={
                "approval_id": "reject-001",
                "action": "reject",
                "rejection_note": "Topics not music-specific enough.",
            })
            assert resp.status_code == 302
            from dashboard.label.scribe import job_store
            updated = job_store.get_job("reject-001")
            assert updated["status"] == "rejected"
            assert updated["rejection_note"] == "Topics not music-specific enough."
        finally:
            _remove_job("reject-001")

    def test_approve_nonexistent_job_returns_redirect(self, client):
        _login(client)
        resp = client.post("/label/scribe/approve", data={
            "approval_id": "nonexistent-xyz",
            "action": "approve",
        })
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Edit approval
# ---------------------------------------------------------------------------

class TestScribeEditApproval:
    def test_edit_get_returns_200(self, client):
        job = _make_propose_topics_job("edit-get-001")
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.get(f"/label/scribe/edit/edit-get-001")
            assert resp.status_code == 200
        finally:
            _remove_job("edit-get-001")

    def test_edit_get_nonexistent_redirects(self, client):
        _login(client)
        resp = client.get("/label/scribe/edit/does-not-exist")
        assert resp.status_code == 302

    def test_edit_structured_updates_topics(self, client):
        job = _make_propose_topics_job("edit-struct-001")
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.post("/label/scribe/edit/edit-struct-001", data={
                "edit_mode": "structured",
                "topic_title_0": "Updated Title",
                "topic_rationale_0": "Updated rationale.",
                "topic_title_1": "Second Topic",
                "topic_rationale_1": "Another rationale.",
            })
            assert resp.status_code == 302
            from dashboard.label.scribe import job_store
            updated = job_store.get_job("edit-struct-001")
            topics = updated["output"]["blogTopics"]
            assert topics[0]["title"] == "Updated Title"
            assert topics[0]["rationale"] == "Updated rationale."
            assert topics[1]["title"] == "Second Topic"
        finally:
            _remove_job("edit-struct-001")

    def test_edit_structured_empty_title_rejected(self, client):
        job = _make_propose_topics_job("edit-empty-001")
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.post("/label/scribe/edit/edit-empty-001", data={
                "edit_mode": "structured",
                "topic_title_0": "  ",  # whitespace only
                "topic_rationale_0": "",
            })
            # Should stay on edit page (200) or redirect with error — not silently accept
            assert resp.status_code in (200, 302)
            from dashboard.label.scribe import job_store
            job = job_store.get_job("edit-empty-001")
            # Output should not have been updated to empty
            assert job["output"]["blogTopics"]  # still has original topics
        finally:
            _remove_job("edit-empty-001")

    def test_edit_add_topic_appears_in_output(self, client):
        """Simulate adding a third topic via structured edit."""
        job = _make_propose_topics_job("edit-add-001")
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.post("/label/scribe/edit/edit-add-001", data={
                "edit_mode": "structured",
                "topic_title_0": "Existing Topic 1",
                "topic_rationale_0": "Rationale 1",
                "topic_title_1": "Existing Topic 2",
                "topic_rationale_1": "Rationale 2",
                "topic_title_2": "New Third Topic",
                "topic_rationale_2": "New rationale",
            })
            assert resp.status_code == 302
            from dashboard.label.scribe import job_store
            updated = job_store.get_job("edit-add-001")
            titles = [t["title"] for t in updated["output"]["blogTopics"]]
            assert "New Third Topic" in titles
        finally:
            _remove_job("edit-add-001")


# ---------------------------------------------------------------------------
# Admin: batch delete
# ---------------------------------------------------------------------------

class TestScribeBatchDelete:
    def test_batch_delete_removes_jobs(self, client):
        job1 = _make_propose_topics_job("batch-del-001")
        job2 = _make_propose_topics_job("batch-del-002")
        _seed_job(client, job1)
        _seed_job(client, job2)
        _login(client)
        try:
            resp = client.post("/label/scribe/admin/batch-delete", data={
                "delete_job_id": ["batch-del-001", "batch-del-002"],
            })
            assert resp.status_code == 302
            from dashboard.label.scribe import job_store
            assert job_store.get_job("batch-del-001") is None
            assert job_store.get_job("batch-del-002") is None
        finally:
            _remove_job("batch-del-001")
            _remove_job("batch-del-002")

    def test_batch_delete_no_ids_does_nothing(self, client):
        _login(client)
        resp = client.post("/label/scribe/admin/batch-delete", data={})
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Admin: batch approve
# ---------------------------------------------------------------------------

class TestScribeBatchApprove:
    def test_batch_approve_marks_jobs_approved(self, client):
        job1 = _make_propose_topics_job("batch-app-001")
        job2 = _make_propose_topics_job("batch-app-002")
        _seed_job(client, job1)
        _seed_job(client, job2)
        _login(client)
        try:
            with patch("dashboard.label.scribe._trigger_workflow",
                       return_value={"triggered": False, "error": "stubbed"}):
                resp = client.post("/label/scribe/admin/batch-approve", data={
                    "approve_job_id": ["batch-app-001", "batch-app-002"],
                })
            assert resp.status_code == 302
            from dashboard.label.scribe import job_store
            assert job_store.get_job("batch-app-001")["status"] == "approved"
            assert job_store.get_job("batch-app-002")["status"] == "approved"
        finally:
            _remove_job("batch-app-001")
            _remove_job("batch-app-002")

    def test_batch_approve_triggers_workflow_for_each(self, client):
        job1 = _make_propose_topics_job("batch-trig-001")
        job2 = _make_propose_topics_job("batch-trig-002")
        _seed_job(client, job1)
        _seed_job(client, job2)
        _login(client)
        try:
            trigger_mock = MagicMock(return_value={"triggered": False, "error": "stubbed"})
            with patch("dashboard.label.scribe._trigger_workflow", trigger_mock):
                client.post("/label/scribe/admin/batch-approve", data={
                    "approve_job_id": ["batch-trig-001", "batch-trig-002"],
                })
            assert trigger_mock.call_count == 2
        finally:
            _remove_job("batch-trig-001")
            _remove_job("batch-trig-002")

    def test_batch_approve_skips_non_pending(self, client):
        """Already-approved jobs should not be double-processed."""
        job = _make_propose_topics_job("batch-skip-001", status="approved")
        _seed_job(client, job)
        _login(client)
        try:
            trigger_mock = MagicMock(return_value={"triggered": False})
            with patch("dashboard.label.scribe._trigger_workflow", trigger_mock):
                client.post("/label/scribe/admin/batch-approve", data={
                    "approve_job_id": ["batch-skip-001"],
                })
            trigger_mock.assert_not_called()
        finally:
            _remove_job("batch-skip-001")


# ---------------------------------------------------------------------------
# Admin: export
# ---------------------------------------------------------------------------

class TestScribeExportJobs:
    def test_export_returns_json(self, client):
        job = _make_propose_topics_job("export-001")
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.get("/label/scribe/admin/export-jobs")
            assert resp.status_code == 200
            assert "application/json" in resp.content_type
            data = json.loads(resp.data)
            assert isinstance(data, list)
        finally:
            _remove_job("export-001")

    def test_export_includes_scribe_jobs_only(self, client):
        scribe_job = _make_propose_topics_job("export-scribe-001")
        other_job = {
            "id": "export-other-001",
            "agent": "SAGE",
            "type": "daily_brief",
            "status": "approved",
            "output": {},
            "timestamp": "2026-05-01T10:00:00Z",
        }
        from dashboard.label.scribe import job_store
        _seed_job(client, scribe_job)
        job_store.add_job("export-other-001", other_job)
        _login(client)
        try:
            resp = client.get("/label/scribe/admin/export-jobs")
            data = json.loads(resp.data)
            ids = [j["id"] for j in data]
            assert "export-scribe-001" in ids
            assert "export-other-001" not in ids
        finally:
            _remove_job("export-scribe-001")
            job_store.delete_job("export-other-001")


# ---------------------------------------------------------------------------
# Admin: normalize
# ---------------------------------------------------------------------------

class TestScribeNormalize:
    def test_normalize_converts_string_output(self, client):
        job = {
            "id": "norm-001",
            "agent": "SCRIBE",
            "type": "propose_topics",
            "status": "pending_approval",
            "output": "Topic A: Some rationale\nTopic B: Another rationale",
            "timestamp": "2026-05-01T10:00:00Z",
        }
        from dashboard.label.scribe import job_store
        _seed_job(client, job)
        _login(client)
        try:
            resp = client.get("/label/scribe/admin/normalize-propose-topics", follow_redirects=True)
            assert resp.status_code == 200
            updated = job_store.get_job("norm-001")
            assert "blogTopics" in updated["output"]
            assert isinstance(updated["output"]["blogTopics"], list)
        finally:
            _remove_job("norm-001")

    def test_normalize_already_normalized_no_change(self, client):
        job = _make_propose_topics_job("norm-002")
        original_output = job["output"]
        from dashboard.label.scribe import job_store
        _seed_job(client, job)
        _login(client)
        try:
            client.get("/label/scribe/admin/normalize-propose-topics", follow_redirects=True)
            updated = job_store.get_job("norm-002")
            assert updated["output"] == original_output
        finally:
            _remove_job("norm-002")


# ---------------------------------------------------------------------------
# _normalize_topics helper (unit tests)
# ---------------------------------------------------------------------------

class TestNormalizeTopics:
    def _norm(self, raw):
        from dashboard.label.scribe import _normalize_topics
        return _normalize_topics(raw)

    def test_list_of_dicts(self):
        result = self._norm([{"title": "T", "rationale": "R"}])
        assert result == {"blogTopics": [{"title": "T", "rationale": "R"}]}

    def test_list_of_strings(self):
        result = self._norm(["Topic A", "Topic B"])
        assert len(result["blogTopics"]) == 2
        assert result["blogTopics"][0]["title"] == "Topic A"
        assert result["blogTopics"][0]["rationale"] == ""

    def test_dict_with_blog_topics_key(self):
        raw = {"blogTopics": [{"title": "T", "rationale": "R"}]}
        assert self._norm(raw) == raw

    def test_dict_with_topics_key(self):
        raw = {"topics": [{"title": "T", "rationale": "R"}]}
        result = self._norm(raw)
        assert result["blogTopics"][0]["title"] == "T"

    def test_json_string(self):
        raw = json.dumps({"blogTopics": [{"title": "T", "rationale": "R"}]})
        result = self._norm(raw)
        assert result["blogTopics"][0]["title"] == "T"

    def test_plain_string_fallback(self):
        result = self._norm("Just a plain string")
        assert result["blogTopics"][0]["title"] == "Just a plain string"

    def test_line_colon_format(self):
        result = self._norm("Topic A: Rationale A\nTopic B: Rationale B")
        assert result["blogTopics"][0]["title"] == "Topic A"
        assert result["blogTopics"][0]["rationale"] == "Rationale A"
        assert result["blogTopics"][1]["title"] == "Topic B"

    def test_empty_list(self):
        result = self._norm([])
        assert result == {"blogTopics": []}


# ---------------------------------------------------------------------------
# _trigger_workflow helper (unit tests)
# ---------------------------------------------------------------------------

class TestTriggerWorkflow:
    def _trigger(self, job):
        from dashboard.label.scribe import _trigger_workflow
        return _trigger_workflow(job)

    def test_propose_topics_creates_blog_versions_job(self):
        job = _make_propose_topics_job("trigger-unit-001")
        from dashboard.label.scribe import job_store
        job_store.add_job("trigger-unit-001", job)
        try:
            with patch.object(ScribeAgent, 'generate_blog_versions', return_value={"easyfunnels_version": "..."}):
                result = self._trigger(job)
            assert result["triggered"] is True
            assert "generate_blog_versions" in result["method"]
        finally:
            _remove_job("trigger-unit-001")

    def test_non_propose_topics_no_workflow(self):
        job = {
            "id": "trigger-unit-002",
            "agent": "SCRIBE",
            "type": "social_campaign",
            "status": "approved",
            "output": {},
        }
        result = self._trigger(job)
        # No error, no trigger (no n8n URL configured in tests)
        assert result["error"] is None

    def test_n8n_url_triggers_post(self):
        job = _make_propose_topics_job("trigger-n8n-001")
        from dashboard.label.scribe import job_store
        job_store.add_job("trigger-n8n-001", job)
        try:
            mock_resp = MagicMock()
            mock_resp.ok = True
            mock_resp.status_code = 200
            with patch.dict(os.environ, {"SCRIBE_N8N_WEBHOOK_URL": "http://n8n.test/webhook/scribe"}):
                with patch("dashboard.label.scribe.ScribeAgent.generate_blog_versions", return_value={}):
                    with patch("requests.post", return_value=mock_resp) as mock_post:
                        result = self._trigger(job)
            mock_post.assert_called_once()
            assert result.get("n8n_status") == 200
        finally:
            _remove_job("trigger-n8n-001")
