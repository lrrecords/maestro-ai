
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