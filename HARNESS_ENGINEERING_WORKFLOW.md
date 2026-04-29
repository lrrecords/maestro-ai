This repository is designed for long-running coding-agent work in the maestro-ai system, which orchestrates multiple agent types (see crews/ and agents/). The goal is to leave the repo in a state where the next session—human or agent—can continue without guessing.

Startup Workflow
Before writing code:

1. Confirm the working directory with `pwd`.
2. Read `claude-progress.md` for the latest verified state and next step.
3. Read `feature_list.json` and choose the highest-priority unfinished feature.
4. Review recent commits with `git log --oneline -5`.
5. Run `./init.sh` (or `start_maestro_session.ps1` on Windows).
6. Run `python test_agents.py` to verify baseline agent functionality.

If baseline verification is already failing, fix that first. Do not stack new feature work on top of a broken starting state.

Working Rules
- Work on one feature at a time.
- Do not mark a feature complete just because code was added.
- Keep changes within the selected feature scope unless a blocker forces a narrow supporting fix.
- Do not silently change verification rules during implementation.
- Prefer durable repo artifacts (feature_list.json, claude-progress.md) over chat summaries.

Required Artifacts
- feature_list.json: source of truth for feature state
- claude-progress.md: session log and current verified status
- init.sh: standard startup and verification path
- session-handoff.md: optional compact handoff for larger sessions (summarize in-progress features, blockers, and next steps for the next agent or human contributor)

Definition Of Done
A feature is done only when all of the following are true:

- The target behavior is implemented
- The required verification (e.g., `python test_agents.py`) actually ran
- Evidence is recorded in feature_list.json or claude-progress.md
- The repository remains restartable from the standard startup path

End Of Session
Before ending a session:

1. Update claude-progress.md.
2. Update feature_list.json.
3. Record any unresolved risk or blocker.
4. Commit with a descriptive message once the work is in a safe state.
5. Leave the repo clean enough for the next session to run ./init.sh (or start_maestro_session.ps1) immediately.
6. Optionally, create a session-handoff.md if the next session will be large or complex.

---

### Workflow Automation & Practices

This repository uses a set of automated tools and scripts to ensure every session—human or agent—runs smoothly and leaves the repo in a reliable state.

**Automated Checks and Scripts:**
- **CI/CD Pipeline:** On every push or pull request, the repository runs baseline verification (`python test_agents.py`) and checks that key artifacts (`feature_list.json`, `claude-progress.md`) are updated. (See `.github/workflows/ci.yml`)
- **Pre-commit Hook:** Before every commit, a script verifies the baseline and ensures artifacts are not stale. (See `.githooks/pre-commit`; copy or symlink to `.git/hooks/pre-commit` and make executable.)
- **Agent Automation:** The script `scripts/agent_automation.py` can auto-update logs, enforce feature state, and capture test evidence.
- **Session Handoff:** Run `scripts/generate_session_handoff.sh` at session end to draft a handoff note from recent changes.
- **VS Code Tasks:** Use the built-in tasks (Ctrl+Shift+P → “Tasks: Run Task”) for startup, verification, and handoff editing.
- **Status Dashboard:** See `STATUS.md` for a summary and CI badge.

**Best Practices:**
- Always run `./init.sh` (or `start_maestro_session.ps1` on Windows) before starting work.
- Only one feature should be `in_progress` in `feature_list.json` at a time.
- Update `claude-progress.md` and `feature_list.json` at the end of every session.
- Use `session-handoff.md` for smooth transitions between sessions.
- Review the Clean State Checklist before ending your session.

**Environment Notes:**
- OS: Windows (PowerShell, Bash, or Git Bash for scripts)
- Editor: VS Code (with Copilot Pro)
- CI/CD: GitHub Actions (enabled by default)
- If you use another editor or shell, adapt scripts as needed.
