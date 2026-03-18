"""
Unified MAESTRO ecosystem dashboard entrypoint.

Run from repo root:
    python -m dashboard.app

Routes:
  /          → department selector
  /maestro/  → MAESTRO dashboard (from scripts.web_app)
  /live/     → LIVE dashboard
  /studio/   → STUDIO dashboard
"""

import os
from flask import Flask, redirect, render_template_string

from scripts.web_app import create_app as create_maestro_app
from live.web import live_bp
from studio.web import studio_bp


DEPT_SELECTOR_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>MAESTRO Ecosystem — Departments</title>
    <style>
      body { background:#0d0d0d; color:#d8d8d8; font-family: system-ui, Segoe UI, sans-serif; padding: 32px; }
      .wrap { max-width: 860px; margin: 0 auto; }
      h1 { color:#f0f0f0; margin: 0 0 10px; }
      p  { color:#888; margin: 0 0 22px; line-height: 1.6; }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
      a.card {
        display:block; text-decoration:none;
        background:#141414; border:1px solid #2a2a2a; border-radius:12px;
        padding:18px; color:#d8d8d8;
        transition: transform .12s, border-color .12s;
      }
      a.card:hover { transform: translateY(-2px); border-color:#007a82; }
      .kicker { font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; color:#555; margin-bottom:10px; }
      .title  { font-size:1.1rem; font-weight:700; color:#f0f0f0; margin-bottom:6px; }
      .desc   { font-size:.85rem; color:#888; line-height:1.5; }
      .tag    { display:inline-block; margin-top:12px; font-size:.7rem; padding:2px 8px; border-radius:999px; }
      .tag-live    { color:#00e5b0; border:1px solid rgba(0,229,176,.35); }
      .tag-maestro { color:#00c8d4; border:1px solid rgba(0,200,212,.35); }
    </style>
  </head>
  <body>
    <div class="wrap">
      <h1>Departments</h1>
      <p>Select a department to open its dashboard.</p>
      <div class="grid">
        <a class="card" href="/maestro/">
          <div class="kicker">Department</div>
          <div class="title">MAESTRO</div>
          <div class="desc">Label ops: releases, social, analytics, automation, strategy, artist health.</div>
          <span class="tag tag-maestro">Available</span>
        </a>
        <a class="card" href="/live/">
          <div class="kicker">Department</div>
          <div class="title">LIVE</div>
          <div class="desc">Live music ops: booking, merch, promo, routing, settlement, riders, tour strategy.</div>
          <span class="tag tag-live">Available</span>
        </a>
        <a class="card" href="/studio/">
          <div class="kicker">Department</div>
          <div class="title">STUDIO</div>
          <div class="desc">Studio ops: client relations, sessions, licensing, marketing, pricing/contracts, mix strategy.</div>
          <span class="tag tag-live">Available</span>
        </a>
      </div>
    </div>
  </body>
</html>
"""


def create_unified_app() -> Flask:
    # Mount MAESTRO at /maestro — this returns the base Flask app instance
    app = create_maestro_app(url_prefix="/maestro")

    # Register LIVE and STUDIO as proper blueprints
    app.register_blueprint(live_bp, url_prefix="/live")
    app.register_blueprint(studio_bp, url_prefix="/studio")

    @app.route("/")
    def departments():
        return render_template_string(DEPT_SELECTOR_HTML)

    @app.route("/maestro")
    def maestro_no_slash():
        return redirect("/maestro/", code=302)

    return app


app = create_unified_app()

if __name__ == "__main__":
    port = int(os.getenv("WEB_PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)