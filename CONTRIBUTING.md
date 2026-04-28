# Contributing to Maestro AI (LABEL)

We 💜 contributions from the label, studio, and indie music tech community!

---

## Getting Started

- Read [README.md](./README.md) for platform overview, quickstart, and config basics.
- Clone this repo and follow setup to install dependencies and run the Flask server.
- Review `.env.example` for configuration options.

---

## Coding Standards

- Use readable Python 3.8+ (PEP8). JS/HTML: ES6+ and clean semantic markup.
- Name artist slugs and agent ids clearly and match across data/UI/backend.
- UI: All user actions MUST check slug selection before firing any API.
- Backend: All endpoints must validate inputs and provide clear error JSON.

---

## Testing & Validation

- All new endpoints require a backend test in `/tests/` (see `test_api.py`).
- Run tests with:
    ```bash
    pytest
    ```
- LLM/agent handlers: test error messages for user guidance. See `test_llm_client.py`.
- Ensure test coverage for special/edge cases whenever possible.

---


## Adding Agents, Plugins, or Pipelines

- Extend `/core` for new agent types or runners.
- Register new agents in the appropriate department module or config.
- Add CLI scripts to `/scripts/` if automating workflows.
- For plugins/extensions, see [docs/EXTENDING.md](docs/EXTENDING.md).

---

## UI/UX Changes

- Edit `/templates/index.html` or related Jinja templates.
- Keep `STATE.slug`/slug guards for all artist actions!
- Add a screenshot to `/docs/assets` if UI is redesigned.

---

## Submitting PRs

- Fork, branch (`feature/xyz`), commit clear messages.
- Write or update tests for your changes.
- Document your code/comment as needed.
- Open PR with context and link to any related issue.
- Someone will review and merge after basic checks.

---


## Open Core & Branding Compliance

- This project is Open Core compliant. Premium/proprietary features are separated and may be disabled via `.env`.
- Do not use Maestro AI or LRRecords branding for proprietary/premium features without written permission.

## Need Help?

- Open an issue in GitHub (“question” label) or ping @lrrecords.
- See [README.md](README.md) for FAQ and troubleshooting steps.