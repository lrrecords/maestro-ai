# Extending Maestro AI (Open Core)

Maestro AI is designed for easy extension via new agents, plugins, and integrations. This guide covers how to add your own agents (open or premium), and how to contribute plugins or extensions.

---

## 1. Adding a New Agent

- Place your agent in the appropriate directory:
  - Open core: `agents/`, `studio/agents/`, `live/agents/`
  - Premium: `premium_agents/` (requires `PREMIUM_FEATURES_ENABLED=true` in `.env`)
- Ensure your agent class inherits from `BaseAgent` (see `core/base_agent.py`).
- Add any required dependencies to `requirements.txt`.
- Agents are auto-discovered via the dynamic loader—no manual registration needed.

## 2. Creating Plugins/Extensions

- Use extension points documented in `core/agent_loader.py` and `dashboard/app.py`.
- Third-party agents can be distributed as Python packages—just ensure they are importable and follow the agent interface.
- Document your extension and provide usage examples.

## 3. Disabling/Enabling Premium Features

- Set `PREMIUM_FEATURES_ENABLED=false` in `.env` to disable loading of premium agents.
- The open core will run without any premium code present.

## 4. Branding & Compliance

- Do not use LRRecords or Maestro AI branding for proprietary/premium features without permission.
- Open core is MIT licensed; premium code may have additional restrictions.

## 5. Contributing Back

- PRs for new agents, plugins, or docs are welcome!
- See `CONTRIBUTING.md` for guidelines.

---

For questions, open an issue or contact the maintainers.
