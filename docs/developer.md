---

### **B. DEVELOPER.md**

```markdown name=DEVELOPER.md
# Developer Guide: Maestro AI

## Repository Structure

- `/dashboard` — Flask app, endpoints, blueprints
- `/core` — LLM agent base classes, extensibility points
- `/templates` & `/static` — HTML, CSS, and JS (dashboard)
- `/tests` — Automated pytest test coverage
- `/docs/assets` — Screenshots and logos for docs & demo

## Adding Departments or Agents

- Add new blueprints to `/dashboard/` for each department (see `label_bp`, `studio_bp`, etc.).
- Create agent modules in `/core/` and register as needed.
- UI changes: update `/templates/index.html`. Every per-artist user action must check `STATE.slug`.

## Backend

- All API endpoints must validate slugs, prevent `/undefined`, and return clear JSON responses.
- Add tests in `/tests/`—if endpoint is broken, fix test or stub until implemented.

## Frontend

- Use toast/alert for all error or success messages (see `toast()` in `index.html`).
- Live updates and transitions: keep navigation intuitive and instant.
- For major UI changes, add screenshots to `docs/assets`.

## Testing

- Run `pytest` before every major commit.
- Add test cases for any new endpoint, especially those that take user or artist input.

## Deployment

- For prod, use Gunicorn or similar.
- Use Docker if deploying widely (see example Dockerfile, if included).
- Never hardcode secrets; always use env vars.

## Contact

- For codebase questions: @lrrecords on GitHub

---

## FOCUS Brief API & Widget (v1.5.0)

### Overview
- Aggregates operational signals (approvals, missions, shows, etc.) for the CEO dashboard.
- Data sources are fully configurable via `dashboard/label/focus_config.py`.
- Endpoint: `GET /label/api/focus/brief` (rate-limited, robust error handling).
- Widget UI: See `templates/hub.html` for loading, error, and headline display.

### How to Add/Change Data Sources
- Edit `dashboard/label/focus_config.py`:
  - To add a new loader: `{"name": "my_source", "loader": "my.module.my_func", "summary_key": "my_key"}`
  - To add a new file: `{"name": "my_file", "path": "data/my_file.json", "summary_key": "my_file"}`
- No code changes needed—just update the config and restart Flask.

### Error Handling
- If any source fails, the endpoint returns HTTP 500 and a JSON error.
- Widget UI displays error state and disables the spinner.

### Testing
- See `tests/test_focus_brief.py` for deterministic tests.
- Patch the correct loader path (e.g., `crews.base_crew.get_pending_approvals`) for error simulation.

### Rate Limiting
- Configured via Flask-Limiter in `dashboard/app.py` (default: 10/min per IP for this endpoint).

---