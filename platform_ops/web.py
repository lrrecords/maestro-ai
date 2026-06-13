# platform_ops/web.py
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests as req
from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

platform_bp = Blueprint("platform", __name__)

SETTINGS_DIR = Path(__file__).parent / "data"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = SETTINGS_DIR / "platform_settings.json"

DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://127.0.0.1:5678/webhook/health-update")
DEFAULT_N8N_BASE_URL = "http://127.0.0.1:5678"

DEFAULT_SETTINGS = {
    "llm": {
        "provider": "ollama",
    "base_url": DEFAULT_OLLAMA_BASE_URL,
        "model": "qwen2.5:3b",
        "temperature": 0.2,
        "num_ctx": 8192,
        "timeout_seconds": 900,
    },
    "integrations": {
        "n8n_base_url": None,
    "webhook_url": DEFAULT_WEBHOOK_URL,
    },
}


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(cfg: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def login_required(f):
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        print("Session state:", session.get("authenticated"))  # Debug log
        if not session.get("authenticated"):
            # Redirect to the main login page, preserving the current path
            return redirect(f"/login?next={request.path}")
        return f(*args, **kwargs)

    return wrapped


def _detect_n8n_base_url(cfg: dict) -> str:
    base = cfg.get("integrations", {}).get("n8n_base_url")
    if base:
        return base

    env_base = (os.getenv("N8N_BASE_URL") or "").strip()
    if env_base:
        return env_base

    webhook_url = cfg.get("integrations", {}).get("webhook_url") or os.getenv("WEBHOOK_URL")
    if webhook_url:
        parts = urlsplit(webhook_url)
        return urlunsplit((parts.scheme, parts.netloc, "", "", ""))

    return DEFAULT_N8N_BASE_URL


@platform_bp.route("/")
@login_required
def index():
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>PLATFORM OPS</title>
  <style>
    body {
      background:#0d0d0d;
      color:#d8d8d8;
      font-family:system-ui,Segoe UI,sans-serif;
      padding:24px;
    }
    .wrap {
      max-width:980px;
      margin:0 auto;
    }
    h1 {
      color:#f0f0f0;
      margin:0 0 14px;
    }
    p {
      color:#888;
      margin:0 0 22px;
      line-height:1.6;
    }
    pre, code {
      font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    }
    .grid {
      display:grid;
      grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
      gap:14px;
    }
    .card {
      background:#141414;
      border:1px solid #2a2a2a;
      border-radius:12px;
      padding:16px;
    }
    .card h3 {
      margin:0 0 8px;
      color:#eaeaea;
    }
    .kv {
      display:flex;
      justify-content:space-between;
      font-size:.9rem;
      margin:4px 0;
    }
    .status {
      display:inline-block;
      padding:2px 8px;
      border-radius:999px;
      font-size:.75rem;
    }
    .ok {
      color:#00e5b0;
      border:1px solid rgba(0,229,176,.35);
    }
    .bad {
      color:#ff6b6b;
      border:1px solid rgba(255,107,107,.35);
    }
    .muted {
      color:#888;
    }
    button {
      background:#1b1b1b;
      color:#eaeaea;
      border:1px solid #2a2a2a;
      border-radius:8px;
      padding:8px 12px;
      cursor:pointer;
    }
    input, select {
      background:#0f0f0f;
      color:#eaeaea;
      border:1px solid #2a2a2a;
      border-radius:8px;
      padding:8px;
      width:100%;
    }
    label {
      display:block;
      font-size:.85rem;
      color:#aaa;
      margin:10px 0 6px;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <a class="back" href="/hub">← Departments</a>
    <h1>PLATFORM OPS — Orchestration, settings, integrations, evals, system health.</h1>
    <p class="muted">Centralized controls for model configuration, service health, and shared platform operations.</p>

    <div class="grid">
      <div class="card">
        <h3>LLM Settings</h3>

        <label>Provider</label>
        <select id="provider">
          <option value="ollama">Ollama (local)</option>
          <option value="anthropic">Anthropic</option>
        </select>
        <p class="muted" style="font-size:.8rem; margin:8px 0 0;">
          Anthropic API keys are read from server environment secrets (`ANTHROPIC_API_KEY`), not entered here.
        </p>

        <label>Base URL</label>
        <input id="base_url" placeholder="http://127.0.0.1:11434"/>

        <label>Model</label>
        <input id="model" placeholder="qwen2.5:3b"/>

        <label>Temperature</label>
        <input id="temperature" type="number" step="0.05" min="0" max="1" placeholder="0.2"/>

        <label>Context Window</label>
        <input id="num_ctx" type="number" step="1" min="512" placeholder="8192"/>

        <label>Timeout Seconds</label>
        <input id="timeout_seconds" type="number" step="1" min="30" placeholder="900"/>

        <div style="margin-top:10px;">
          <button onclick="saveSettings()">Save</button>
          <button onclick="refreshSettings()">Reset</button>
        </div>
        <p id="action-status" class="muted" style="font-size:.8rem; margin:8px 0 0;"></p>
      </div>

      <div class="card">
        <h3>Service Health</h3>
        <div class="kv"><span>Ollama</span><span id="ollama-status" class="status muted">checking…</span></div>
        <div class="kv"><span>n8n</span><span id="n8n-status" class="status muted">checking…</span></div>
        <pre id="details" class="muted" style="white-space:pre-wrap; margin-top:10px;"></pre>
        <button onclick="refreshHealth()">Re-check</button>
      </div>
    </div>
  </div>

  <script>
    function setStatus(message, isError = false) {
      const el = document.getElementById("action-status");
      el.textContent = message || "";
      el.style.color = isError ? "#ff6b6b" : "#888";
    }

    async function refreshSettings() {
      try {
        const res = await fetch("/platform/api/settings", { credentials: "same-origin" });
        if (!res.ok) throw new Error(`settings request failed: ${res.status}`);
        const cfg = await res.json();
        const llm = cfg.llm || {};
        document.getElementById("provider").value = llm.provider || "ollama";
        document.getElementById("base_url").value = llm.base_url || "http://127.0.0.1:11434";
        document.getElementById("model").value = llm.model || "qwen2.5:3b";
        document.getElementById("temperature").value = llm.temperature ?? 0.2;
        document.getElementById("num_ctx").value = llm.num_ctx ?? 8192;
        document.getElementById("timeout_seconds").value = llm.timeout_seconds ?? 900;
        setStatus("Settings loaded.");
      } catch (err) {
        setStatus(`Failed to load settings: ${err.message}`, true);
      }
    }

    async function saveSettings() {
      const payload = {
        llm: {
          provider: document.getElementById("provider").value,
          base_url: document.getElementById("base_url").value,
          model: document.getElementById("model").value,
          temperature: parseFloat(document.getElementById("temperature").value),
          num_ctx: parseInt(document.getElementById("num_ctx").value, 10),
          timeout_seconds: parseInt(document.getElementById("timeout_seconds").value, 10)
        }
      };

      try {
        const res = await fetch("/platform/api/settings", {
          method:"POST",
          headers:{ "Content-Type":"application/json" },
          credentials: "same-origin",
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(`save failed: ${res.status}`);
        setStatus("Settings saved.");
        await refreshSettings();
        await refreshHealth();
      } catch (err) {
        setStatus(`Failed to save settings: ${err.message}`, true);
      }
    }

    async function refreshHealth() {
      try {
        const res = await fetch("/platform/api/health", { credentials: "same-origin" });
        if (!res.ok) throw new Error(`health request failed: ${res.status}`);
        const h = await res.json();

        const ollamaEl = document.getElementById("ollama-status");
        const n8nEl = document.getElementById("n8n-status");

        const ollamaOk = Boolean(h.ollama && h.ollama.ok);
        const n8nOk = Boolean(h.n8n && h.n8n.ok);

        ollamaEl.textContent = ollamaOk ? "ok" : "down";
        ollamaEl.className = "status " + (ollamaOk ? "ok" : "bad");

        n8nEl.textContent = n8nOk ? "ok" : "down";
        n8nEl.className = "status " + (n8nOk ? "ok" : "bad");

        document.getElementById("details").textContent = JSON.stringify(h, null, 2);
      } catch (err) {
        setStatus(`Failed to refresh health: ${err.message}`, true);
      }
    }

    refreshSettings();
    refreshHealth();
  </script>
</body>
</html>
    """
    return render_template_string(html)


@platform_bp.route("/api/settings", methods=["GET", "POST"])
@login_required
def api_settings():
    if request.method == "GET":
        return jsonify(load_settings())

    incoming = request.get_json(silent=True) or {}
    cfg = load_settings()

    for section in ("llm", "integrations"):
        if section in incoming and isinstance(incoming[section], dict):
            cfg.setdefault(section, {}).update(incoming[section])

    save_settings(cfg)
    return jsonify({"saved": True, "settings": cfg})


@platform_bp.route("/api/health")
@login_required
def api_health():
    cfg = load_settings()
  llm_provider = str(cfg.get("llm", {}).get("provider", "ollama")).lower().strip()

    ollama = {"ok": False, "models": [], "version": None, "error": None}
    base = cfg.get("llm", {}).get("base_url") or DEFAULT_OLLAMA_BASE_URL

    if llm_provider == "ollama":
        try:
            r = req.get(f"{base.rstrip('/')}/api/tags", timeout=3)
            if r.ok:
                data = r.json()
                ollama["ok"] = True
                ollama["models"] = [m.get("name") for m in data.get("models", [])]

            v = req.get(f"{base.rstrip('/')}/api/version", timeout=3)
            if v.ok:
                ollama["version"] = v.json().get("version")
        except Exception as e:
            ollama["error"] = str(e)
    else:
        ollama = {"ok": True, "models": [], "version": None, "error": f"Skipped (provider={llm_provider})"}

    n8n = {"ok": False, "base_url": None, "error": None}
    n8n_base = _detect_n8n_base_url(cfg)
    n8n["base_url"] = n8n_base

    try:
        h = req.get(f"{n8n_base.rstrip('/')}/health", timeout=3)
        if not h.ok:
            h = req.head(n8n_base, timeout=3)
        n8n["ok"] = h.ok
    except Exception as e:
        n8n["error"] = str(e)

    return jsonify({"ollama": ollama, "n8n": n8n})