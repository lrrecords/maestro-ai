from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from core.job_store import JobStore
from agents.label.scribe.scribe_agent import ScribeAgent

scribe_bp = Blueprint("scribe", __name__)

job_store = JobStore()

# --- Admin route to normalize all propose_topics jobs ---
@scribe_bp.route("/admin/normalize-propose-topics")
def admin_normalize_propose_topics():
    import ast
    import re
    def normalize_topics(raw):
        def to_topic_dict(item):
            if isinstance(item, dict):
                title = item.get('title') or item.get('option') or str(item)
                rationale = item.get('rationale') or item.get('reason') or ''
                return {'title': title, 'rationale': rationale}
            elif isinstance(item, str):
                return {'title': item, 'rationale': ''}
            return {'title': str(item), 'rationale': ''}

        # Handle stringified Python dicts from Ollama
        if isinstance(raw, str):
            s = raw.strip()
            # Try to parse as Python dict if it looks like one
            if (s.startswith('{') and s.endswith('}')) and ("blogTopic" in s or "title" in s):
                try:
                    # Replace single quotes with double quotes for JSON, but only outside of keys
                    # Use ast.literal_eval for safety
                    parsed = ast.literal_eval(s)
                    # If keys are blogTopic1, blogTopic2, ...
                    if all(k.startswith('blogTopic') for k in parsed.keys()):
                        topics = [to_topic_dict(v) for v in parsed.values()]
                        return {'blogTopics': topics}
                    # If it's a dict with title/rationale
                    if 'title' in parsed:
                        return {'blogTopics': [to_topic_dict(parsed)]}
                except Exception:
                    pass
            # Try to parse as JSON if possible
            try:
                import json
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    if 'blogTopics' in parsed and isinstance(parsed['blogTopics'], list):
                        return {'blogTopics': [to_topic_dict(t) for t in parsed['blogTopics']]}
                    if 'topics' in parsed and isinstance(parsed['topics'], list):
                        return {'blogTopics': [to_topic_dict(t) for t in parsed['topics']]}
                    if all(k.startswith('blogTopic') for k in parsed.keys()):
                        topics = [to_topic_dict(v) for v in parsed.values()]
                        return {'blogTopics': topics}
                    if 'title' in parsed:
                        return {'blogTopics': [to_topic_dict(parsed)]}
                if isinstance(parsed, list):
                    return {'blogTopics': [to_topic_dict(t) for t in parsed]}
            except Exception:
                pass
            # Fallback: treat as plain string
            return {'blogTopics': [{'title': raw, 'rationale': ''}]}

        if isinstance(raw, dict):
            if 'blogTopics' in raw and isinstance(raw['blogTopics'], list):
                return {'blogTopics': [to_topic_dict(t) for t in raw['blogTopics']]}
            if 'topics' in raw and isinstance(raw['topics'], list):
                return {'blogTopics': [to_topic_dict(t) for t in raw['topics']]}
            if all(k.startswith('blogTopic') for k in raw.keys()):
                topics = [to_topic_dict(v) for v in raw.values()]
                return {'blogTopics': topics}
            if 'title' in raw:
                return {'blogTopics': [to_topic_dict(raw)]}
            return {'blogTopics': [to_topic_dict(raw)]}
        if isinstance(raw, list):
            return {'blogTopics': [to_topic_dict(t) for t in raw]}
        return {'blogTopics': []}

    jobs = job_store.all_jobs()
    updated = 0
    for job in jobs:
        if job.get('type') == 'propose_topics':
            old_output = job.get('output')
            new_output = normalize_topics(old_output)
            if new_output != old_output:
                job['output'] = new_output
                job_store.add_job(job['id'], job)
                updated += 1
    flash(f"Normalized {updated} propose_topics jobs.", "success")
    return redirect(url_for('scribe.index'))



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

@scribe_bp.route("/")
def index():
    # Dashboard card
    scribe_jobs = [j for j in job_store.all_jobs() if j.get("agent") == "SCRIBE"]
    pending_approvals = [j for j in scribe_jobs if j.get("status") == "pending_approval"]
    last_run = max((j.get("timestamp") for j in scribe_jobs if j.get("timestamp")), default=None)
    status = {
        "status": "Idle" if not pending_approvals else "Pending Approval",
        "last_run": last_run,
        "pending_approvals": len(pending_approvals)
    }
    # Sort jobs by most recent (if you have a timestamp)
    recent_jobs = sorted(scribe_jobs, key=lambda j: j.get("timestamp", ""), reverse=True)[:10]
    return render_template("label/scribe_dashboard.html", status=status, recent_jobs=recent_jobs)

@scribe_bp.route("/approvals")
def approvals():
    # Show all SCRIBE jobs pending approval
    scribe_jobs = [j for j in job_store.all_jobs() if j.get("agent") == "SCRIBE" and j.get("status") == "pending_approval"]
    return render_template("label/scribe_approvals.html", approvals=scribe_jobs)

@scribe_bp.route("/approve", methods=["POST"])
def approve():
    approval_id = request.form.get("approval_id")
    action = request.form.get("action")
    rejection_note = request.form.get("rejection_note")
    job = job_store.get_job(approval_id)
    if not job:
        flash(f"Approval ID {approval_id} not found.", "error")
        return redirect(url_for("scribe.approvals"))
    if action == "approve":
        job["status"] = "approved"
    elif action == "edit":
        job["status"] = "approved"
        # Optionally update job content here
    elif action == "reject":
        job["status"] = "rejected"
        job["rejection_note"] = rejection_note
    job_store.add_job(approval_id, job)
    flash(f"Action '{action}' submitted for approval ID {approval_id}.")
    return redirect(url_for("scribe.approvals"))


# --- Edit Approval Content Route ---
@scribe_bp.route("/edit/<job_id>", methods=["GET", "POST"])
def edit_approval(job_id):
    job = job_store.get_job(job_id)
    if not job:
        flash('Job not found.', 'error')
        return redirect(url_for('scribe.approvals'))
    if request.method == 'POST':
        new_content = request.form.get('content', '').strip()
        if new_content:
            # Normalize if propose_topics
            if job.get('type') == 'propose_topics':
                def normalize_topics(raw):
                    import ast, json
                    def to_topic_dict(item):
                        if isinstance(item, dict):
                            title = item.get('title') or item.get('option') or str(item)
                            rationale = item.get('rationale') or item.get('reason') or ''
                            return {'title': title, 'rationale': rationale}
                        elif isinstance(item, str):
                            return {'title': item, 'rationale': ''}
                        return {'title': str(item), 'rationale': ''}
                    s = raw.strip()
                    # Try to parse as Python dict if it looks like one
                    parsed = None
                    if (s.startswith('{') and s.endswith('}')):
                        try:
                            parsed = ast.literal_eval(s)
                        except Exception:
                            pass
                    if parsed is None:
                        try:
                            parsed = json.loads(s)
                        except Exception:
                            pass
                    # If parsed is a dict with topic1, topic2, ... keys, convert to blogTopics
                    if isinstance(parsed, dict):
                        if all(k.lower().startswith('topic') for k in parsed.keys()):
                            topics = [to_topic_dict(v) for v in parsed.values()]
                            return {'blogTopics': topics}
                        if 'blogTopics' in parsed and isinstance(parsed['blogTopics'], list):
                            return {'blogTopics': [to_topic_dict(t) for t in parsed['blogTopics']]}
                        if 'topics' in parsed and isinstance(parsed['topics'], list):
                            return {'blogTopics': [to_topic_dict(t) for t in parsed['topics']]}
                        if 'title' in parsed:
                            return {'blogTopics': [to_topic_dict(parsed)]}
                    if isinstance(parsed, list):
                        return {'blogTopics': [to_topic_dict(t) for t in parsed]}
                    # Fallback: treat as plain string with possible multiple lines in 'title: rationale' format
                    lines = [line for line in raw.split('\n') if line.strip()]
                    topics = []
                    for line in lines:
                        parts = line.split(':', 1)
                        title = parts[0].strip()
                        rationale = parts[1].strip() if len(parts) > 1 else ''
                        topics.append({'title': title, 'rationale': rationale})
                    return {'blogTopics': topics}
                job['output'] = normalize_topics(new_content)
            else:
                job['output'] = new_content
            job_store.add_job(job_id, job)
            flash('Content updated.', 'success')
            return redirect(url_for('scribe.approvals'))
        else:
            flash('Content cannot be empty.', 'error')
    return render_template('label/scribe_edit_approval.html', job=job)

@scribe_bp.route("/propose-topics", methods=["POST"])
def propose_topics():
    topic_preferences = request.form.get("topic_preferences", "").strip()
    llm_choice = request.form.get("llm_choice", "anthropic")
    agent = ScribeAgent(job_store, llm_provider=llm_choice)
    result = agent.propose_topics(topic_preferences=topic_preferences)
    flash("Blog topic options generated and submitted for CEO approval.", "success")
    return redirect(url_for("scribe.index"))