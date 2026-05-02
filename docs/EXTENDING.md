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

### Minimal agent example

```python
# agents/my_agent.py
from core.base_agent import BaseAgent

class MyAgent(BaseAgent):
    name = "MyAgent"
    description = "Describe what your agent does."

    def run(self, context: dict) -> dict:
        # context is a free-form dict passed from the caller
        return {
            "status": "complete",
            "data": {
                "message": f"Hello from MyAgent! context={context}",
            },
        }
```

Once placed in `agents/` the agent is immediately available at:

- `GET /agents` — appears in the agent list
- `POST /agents/run/MyAgent` — executes it and returns JSON

### Agent interface contract

All agents must return a dict with at least:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `status` | `str` | ✅ | `"complete"` on success, `"error"` on failure |
| `data` | `dict` | ✅ | Structured output payload |
| `message` | `str` | — | Optional human-readable summary |

---

## 2. Premium Agents

Place premium agents in `premium_agents/` and guard all imports:

```python
# premium_agents/my_premium_agent.py
from core.base_agent import BaseAgent

class MyPremiumAgent(BaseAgent):
    name = "MyPremiumAgent"

    def run(self, context: dict) -> dict:
        ...
```

Enable with `PREMIUM_FEATURES_ENABLED=true` in `.env`.
If the flag is `false` or the file is absent, the agent loader logs a warning and continues—the rest of the platform is unaffected.

---

## 3. Adding a Dashboard Page for Your Agent

1. Add a route in `dashboard/app.py` (or a new Blueprint):

```python
@app.route("/agents/my-agent", methods=["GET", "POST"])
@login_required
def agent_my_agent():
    result = error = None
    if request.method == "POST":
        try:
            from agents.my_agent import MyAgent
            result = MyAgent().run(dict(request.form))
        except Exception as exc:
            error = str(exc)
    return render_template("agents/my_agent.html", result=result, error=error)
```

2. Create `templates/agents/my_agent.html` using the existing agent templates as a reference (e.g., `templates/agents/focus.html`).

---

## 4. Creating Plugins/Extensions

- Use the extension points in `core/agent_loader.py` and `dashboard/app.py`.
- Third-party agents can be distributed as Python packages—just ensure they are importable and follow the agent interface.
- Document your extension and provide usage examples.

### Packaging as a Python module

```
my_maestro_plugin/
├── __init__.py
├── my_agent.py          # inherits BaseAgent
└── setup.py / pyproject.toml
```

Install with `pip install my_maestro_plugin`, then place in an agents directory or import directly.

---

## 5. Disabling/Enabling Premium Features

```bash
# .env
PREMIUM_FEATURES_ENABLED=false   # open core only
PREMIUM_FEATURES_ENABLED=true    # enable premium agents
```

The open core will run without any premium code present.

---

## 6. Adding Tests for Your Agent

Place tests in `tests/` following the existing patterns:

```python
# tests/test_my_agent.py
from unittest.mock import patch
from agents.my_agent import MyAgent

def test_my_agent_returns_complete():
    result = MyAgent().run({})
    assert result["status"] == "complete"
    assert "message" in result["data"]
```

Run all tests with:

```bash
python -m pytest tests/ -v --tb=short
```

---

## 7. Branding & Compliance

- Do not use LRRecords or Maestro AI branding for proprietary/premium features without permission.
- Open core is MIT licensed; premium code may have additional restrictions.

---

## 8. Contributing Back

- PRs for new agents, plugins, or docs are welcome!
- See `CONTRIBUTING.md` for guidelines.

---

For questions, open an issue or contact the maintainers.
