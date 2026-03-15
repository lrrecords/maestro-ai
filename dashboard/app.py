"""
# Run from repo root:
#   python -m dashboard.app
dashboard/app.py

Unified MAESTRO ecosystem dashboard entrypoint.

Run: python dashboard/app.py
- /          -> department selector
- /maestro/  -> MAESTRO dashboard (mounted from scripts.web_app blueprint)
- /live/     -> placeholder
- /studio/   -> placeholder
"""

import os
from flask import Flask, redirect, render_template_string

from scripts.web_app import create_app as create_maestro_app


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
      .kicker { font-size: .72rem; letter-spacing:.12em; text-transform:uppercase; color:#555; margin-bottom:10px; }
      .title { font-size: 1.1rem; font-weight: 700; color:#f0f0f0; margin-bottom:6px; }
      .desc { font-size:.85rem; color:#888; line-height:1.5; }
      .tag { display:inline-block; margin-top:12px; font-size:.7rem; color:#00c8d4; border:1px solid rgba(0,200,212,.35); padding:2px 8px; border-radius:999px; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <h1>Departments</h1>
      <p>Select a department to open its dashboard. MAESTRO is live; LIVE and STUDIO are scaffolds for upcoming work.</p>
      <div class="grid">
        <a class="card" href="/maestro/">
          <div class="kicker">Department</div>
          <div class="title">MAESTRO</div>
          <div class="desc">Label ops: releases, social, analytics, automation, strategy, artist health.</div>
          <span class="tag">Available</span>
        </a>
        <a class="card" href="/live/">
          <div class="kicker">Department</div>
          <div class="title">LIVE</div>
          <div class="desc">Live music ops: booking, merch, promo, routing, settlement, riders, tour strategy.</div>
          <span class="tag">Coming soon</span>
        </a>
        <a class="card" href="/studio/">
          <div class="kicker">Department</div>
          <div class="title">STUDIO</div>
          <div class="desc">Studio ops: client relations, sessions, licensing, marketing, pricing/contracts, mix strategy.</div>
          <span class="tag">Coming soon</span>
        </a>
      </div>
    </div>
  </body>
</html>
"""


def create_unified_app() -> Flask:
    # Create the MAESTRO app mounted at /maestro
    maestro = create_maestro_app(url_prefix="/maestro")

    # Add department selector + placeholders to the same Flask app
    app = maestro

    @app.route("/")
    def departments():
        return render_template_string(DEPT_SELECTOR_HTML)

    @app.route("/maestro")
    def maestro_no_slash():
        return redirect("/maestro/", code=302)

    @app.route("/live/")
    def live_placeholder():
        return render_template_string("<h1 style='font-family:system-ui;color:#f0f0f0;background:#0d0d0d;padding:32px'>LIVE — Coming soon</h1>")

    @app.route("/studio/")
    def studio_placeholder():
        return render_template_string("<h1 style='font-family:system-ui;color:#f0f0f0;background:#0d0d0d;padding:32px'>STUDIO — Coming soon</h1>")

    return app


app = create_unified_app()

if __name__ == "__main__":
    # Reuse the same port env var as scripts/web_app.py
    port = int(os.getenv("WEB_PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)