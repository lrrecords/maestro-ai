import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from core.job_store import JobStore
from agents.label.scribe.scribe_agent import ScribeAgent

scribe_bp = Blueprint("scribe", __name__)

job_store = JobStore()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _normalize_topics(raw):
    """Normalise any LLM-produced propose_topics output to {'blogTopics': [{title, rationale}]}."""
    import ast

    def to_topic_dict(item):
        if isinstance(item, dict):
            title = item.get('title') or item.get('option') or str(item)
            rationale = item.get('rationale') or item.get('reason') or ''
            return {'title': title, 'rationale': rationale}
        if isinstance(item, str):
            return {'title': item, 'rationale': ''}
        return {'title': str(item), 'rationale': ''}

    if isinstance(raw, str):
        s = raw.strip()
        if (s.startswith('{') and s.endswith('}')) and ("blogTopic" in s or "title" in s):
            try:
                parsed = ast.literal_eval(s)
                if 'blogTopics' in parsed and isinstance(parsed['blogTopics'], list):
                    return {'blogTopics': [to_topic_dict(t) for t in parsed['blogTopics']]}
                if 'topics' in parsed and isinstance(parsed['topics'], list):
                    return {'blogTopics': [to_topic_dict(t) for t in parsed['topics']]}
                if parsed.keys() and all(k.startswith('blogTopic') for k in parsed.keys()):
                    return {'blogTopics': [to_topic_dict(v) for v in parsed.values()]}
                if 'title' in parsed:
                    return {'blogTopics': [to_topic_dict(parsed)]}
            except Exception:
                pass
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                if 'blogTopics' in parsed and isinstance(parsed['blogTopics'], list):
                    return {'blogTopics': [to_topic_dict(t) for t in parsed['blogTopics']]}
                if 'topics' in parsed and isinstance(parsed['topics'], list):
                    return {'blogTopics': [to_topic_dict(t) for t in parsed['topics']]}
                if parsed.keys() and all(k.startswith('blogTopic') for k in parsed.keys()):
                    return {'blogTopics': [to_topic_dict(v) for v in parsed.values()]}
                if 'title' in parsed:
                    return {'blogTopics': [to_topic_dict(parsed)]}
            if isinstance(parsed, list):
                return {'blogTopics': [to_topic_dict(t) for t in parsed]}
        except Exception:
            pass
        lines = [l for l in raw.split('\n') if l.strip()]
        topics = []
        for line in lines:
            parts = line.split(':', 1)
            title = parts[0].strip()
            rationale = parts[1].strip() if len(parts) > 1 else ''
            topics.append({'title': title, 'rationale': rationale})
        return {'blogTopics': topics} if topics else {'blogTopics': [{'title': raw, 'rationale': ''}]}

    if isinstance(raw, dict):
        if 'blogTopics' in raw and isinstance(raw['blogTopics'], list):
            return {'blogTopics': [to_topic_dict(t) for t in raw['blogTopics']]}
        if 'topics' in raw and isinstance(raw['topics'], list):
            return {'blogTopics': [to_topic_dict(t) for t in raw['topics']]}
        if raw.keys() and all(k.startswith('blogTopic') for k in raw.keys()):
            return {'blogTopics': [to_topic_dict(v) for v in raw.values()]}
        if 'title' in raw:
            return {'blogTopics': [to_topic_dict(raw)]}
        return {'blogTopics': [to_topic_dict(raw)]}
    if isinstance(raw, list):
        return {'blogTopics': [to_topic_dict(t) for t in raw]}
    return {'blogTopics': []}


def _trigger_workflow(job):
    """
    Fire the post-approval workflow for a job.

    For propose_topics: kick off generate_blog_versions and (if configured)
    POST a trigger to the SCRIBE n8n webhook.
    Returns a dict with trigger result info.
    """
    result = {"triggered": False, "method": None, "error": None}

    if job.get('type') == 'propose_topics':
        topics = job.get('output', {}).get('blogTopics', [])
        approved_topic = topics[0].get('title', '') if topics else ''
        try:
            agent = ScribeAgent(job_store)
            agent.generate_blog_versions(approved_topic)
            result["triggered"] = True
            result["method"] = "generate_blog_versions"
        except Exception as exc:
            result["error"] = str(exc)
            return result

    n8n_url = os.environ.get("SCRIBE_N8N_WEBHOOK_URL", "").strip()
    if n8n_url:
        try:
            import requests
            payload = {
                "event": "job_approved",
                "job_id": job.get("id"),
                "job_type": job.get("type"),
                "output": job.get("output"),
            }
            resp = requests.post(n8n_url, json=payload, timeout=10)
            result["n8n_status"] = resp.status_code
            result["triggered"] = True
            result["method"] = (result.get("method") or "") + "+n8n"
        except Exception as exc:
            result["n8n_error"] = str(exc)

    return result


# ---------------------------------------------------------------------------
# Admin: normalize all propose_topics jobs
# ---------------------------------------------------------------------------

@scribe_bp.route("/admin/normalize-propose-topics")
def admin_normalize_propose_topics():
    jobs = job_store.all_jobs()
    updated = 0
    for job in jobs:
        if job.get('type') == 'propose_topics':
            old_output = job.get('output')
            new_output = _normalize_topics(old_output)
            if new_output != old_output:
                job['output'] = new_output
                job_store.add_job(job['id'], job)
                updated += 1
    flash(f"Normalized {updated} propose_topics job(s).", "success")
    return redirect(url_for('scribe.index'))


# ---------------------------------------------------------------------------
# Admin: export all SCRIBE jobs as JSON
# ---------------------------------------------------------------------------

@scribe_bp.route("/admin/export-jobs")
def admin_export_jobs():
    scribe_jobs = [j for j in job_store.all_jobs() if j.get("agent") == "SCRIBE"]
    data = json.dumps(scribe_jobs, indent=2)
    return Response(
        data,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=scribe_jobs.json"}
    )


# ---------------------------------------------------------------------------
# Admin: batch delete
# ---------------------------------------------------------------------------

@scribe_bp.route("/admin/batch-delete", methods=["POST"])
def admin_batch_delete():
    job_ids = request.form.getlist("delete_job_id")
    deleted = 0
    for job_id in job_ids:
        if job_store.get_job(job_id):
            job_store.delete_job(job_id)
            deleted += 1
    flash(f"Deleted {deleted} job(s).", "success")
    return redirect(url_for("scribe.index"))


# ---------------------------------------------------------------------------
# Admin: batch approve
# ---------------------------------------------------------------------------

@scribe_bp.route("/admin/batch-approve", methods=["POST"])
def admin_batch_approve():
    job_ids = request.form.getlist("approve_job_id")
    approved = 0
    for job_id in job_ids:
        job = job_store.get_job(job_id)
        if job and job.get("status") == "pending_approval":
            job["status"] = "approved"
            job_store.add_job(job_id, job)
            _trigger_workflow(job)
            approved += 1
    flash(f"Approved {approved} job(s) and triggered workflows.", "success")
    return redirect(url_for("scribe.approvals"))


# ---------------------------------------------------------------------------
# Legacy single-job delete (kept for backward compat)
# ---------------------------------------------------------------------------

@scribe_bp.route("/delete-jobs", methods=["POST"])
def delete_jobs():
    job_ids = request.form.getlist("delete_job_id")
    deleted = 0
    for job_id in job_ids:
        if job_store.get_job(job_id):
            job_store.delete_job(job_id)
            deleted += 1
    flash(f"Deleted {deleted} job(s).", "success")
    return redirect(url_for("scribe.index"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@scribe_bp.route("/")
def index():
    scribe_jobs = [j for j in job_store.all_jobs() if j.get("agent") == "SCRIBE"]
    pending_approvals = [j for j in scribe_jobs if j.get("status") == "pending_approval"]
    last_run = max((j.get("timestamp") for j in scribe_jobs if j.get("timestamp")), default=None)
    status = {
        "status": "Idle" if not pending_approvals else "Pending Approval",
        "last_run": last_run,
        "pending_approvals": len(pending_approvals)
    }
    recent_jobs = sorted(scribe_jobs, key=lambda j: j.get("timestamp", ""), reverse=True)[:10]
    return render_template("label/scribe_dashboard.html", status=status, recent_jobs=recent_jobs)


# ---------------------------------------------------------------------------
# Approval queue
# ---------------------------------------------------------------------------

@scribe_bp.route("/approvals")
def approvals():
    scribe_jobs = [
        j for j in job_store.all_jobs()
        if j.get("agent") == "SCRIBE" and j.get("status") == "pending_approval"
    ]
    return render_template("label/scribe_approvals.html", approvals=scribe_jobs)


# ---------------------------------------------------------------------------
# Approve / reject
# ---------------------------------------------------------------------------

@scribe_bp.route("/approve", methods=["POST"])
def approve():
    approval_id = request.form.get("approval_id")
    action = request.form.get("action")
    rejection_note = request.form.get("rejection_note", "").strip()
    job = job_store.get_job(approval_id)
    if not job:
        flash(f"Job {approval_id} not found.", "error")
        return redirect(url_for("scribe.approvals"))

    if action in ("approve", "edit"):
        job["status"] = "approved"
        job_store.add_job(approval_id, job)
        trigger_result = _trigger_workflow(job)
        if trigger_result.get("triggered"):
            flash(
                f"Job approved and workflow triggered "
                f"(method: {trigger_result.get('method', 'unknown')}).",
                "success"
            )
        else:
            err = trigger_result.get("error") or "no workflow configured"
            flash(f"Job approved. Workflow not triggered: {err}.", "success")
    elif action == "reject":
        job["status"] = "rejected"
        if rejection_note:
            job["rejection_note"] = rejection_note
        job_store.add_job(approval_id, job)
        flash("Job rejected.", "success")
    else:
        flash(f"Unknown action '{action}'.", "error")

    return redirect(url_for("scribe.approvals"))


# ---------------------------------------------------------------------------
# Edit approval content
# ---------------------------------------------------------------------------

@scribe_bp.route("/edit/<job_id>", methods=["GET", "POST"])
def edit_approval(job_id):
    job = job_store.get_job(job_id)
    if not job:
        flash('Job not found.', 'error')
        return redirect(url_for('scribe.approvals'))

    if request.method == 'POST':
        edit_mode = request.form.get('edit_mode', 'raw')

        if edit_mode == 'structured' and job.get('type') == 'propose_topics':
            topics = []
            i = 0
            while True:
                title = request.form.get(f'topic_title_{i}')
                if title is None:
                    break
                title = title.strip()
                rationale = request.form.get(f'topic_rationale_{i}', '').strip()
                if title:
                    topics.append({'title': title, 'rationale': rationale})
                i += 1
            if not topics:
                flash('At least one topic with a title is required.', 'error')
                return render_template('label/scribe_edit_approval.html', job=job)
            job['output'] = {'blogTopics': topics}
            job_store.add_job(job_id, job)
            flash('Topics updated successfully.', 'success')
            return redirect(url_for('scribe.approvals'))

        new_content = request.form.get('content', '').strip()
        if not new_content:
            flash('Content cannot be empty.', 'error')
            return render_template('label/scribe_edit_approval.html', job=job)
        if job.get('type') == 'propose_topics':
            job['output'] = _normalize_topics(new_content)
        else:
            job['output'] = new_content
        job_store.add_job(job_id, job)
        flash('Content updated.', 'success')
        return redirect(url_for('scribe.approvals'))

    return render_template('label/scribe_edit_approval.html', job=job)


# ---------------------------------------------------------------------------
# Propose topics
# ---------------------------------------------------------------------------

@scribe_bp.route("/propose-topics", methods=["POST"])
def propose_topics():
    topic_preferences = request.form.get("topic_preferences", "").strip()
    llm_choice = request.form.get("llm_choice", "anthropic")
    agent = ScribeAgent(job_store, llm_provider=llm_choice)
    agent.propose_topics(topic_preferences=topic_preferences)
    flash("Blog topic options generated and submitted for CEO approval.", "success")
    return redirect(url_for("scribe.index"))
