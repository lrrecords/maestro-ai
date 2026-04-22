import os
import sys
from pathlib import Path
from functools import wraps
from flask import Flask, redirect, render_template, session, request, url_for
# --- Flasgger (Swagger UI) ---
from flasgger import Swagger
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from platform_ops.web import platform_bp
from live.web import live_bp
from studio.web import studio_bp
from label.web import label_bp

TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"


app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR)
)

# --- Flasgger Swagger UI config ---
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # all endpoints
            "model_filter": lambda tag: True,  # all models
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}
swagger = Swagger(app, config=swagger_config)

SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24).hex())
app.secret_key = SECRET_KEY

MAESTRO_TOKEN = (os.getenv("MAESTRO_TOKEN") or "").strip()
MAESTRO_DEV_MODE = os.getenv("MAESTRO_DEV_MODE", "").strip() == "1"

if not MAESTRO_TOKEN and not MAESTRO_DEV_MODE:
    # Don't crash — run in locked mode and show a helpful message on /login
    app.logger.warning(
        "MAESTRO_TOKEN is not set. Dashboard is locked. "
        "Set MAESTRO_TOKEN in .env (recommended) or set MAESTRO_DEV_MODE=1 for local dev."
    )

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

# Register blueprints
app.register_blueprint(platform_bp, url_prefix="/platform")
app.register_blueprint(live_bp, url_prefix="/live")
app.register_blueprint(studio_bp, url_prefix="/studio")
app.register_blueprint(label_bp,   url_prefix="/label")
app.config["LABEL_URL_PREFIX"] = "/label"

@app.route("/")
def index():
    if not session.get("authenticated"):
        return redirect(url_for("login_page", next=request.path))
    return redirect(url_for("hub"))

@app.route("/label")
@login_required
def label_root_alias():
    return redirect(url_for("label.index"))

@app.route("/hub")
@login_required
def hub():
    return render_template("hub.html")

@app.route("/login", methods=["GET", "POST"])
def login_page():
    next_url = request.form.get("next") or request.args.get("next", url_for("hub"))
    error = None

    token_configured = bool(MAESTRO_TOKEN)
    if request.method == "POST":
        token = request.form.get("token", "").strip()

        # Dev bypass: if explicitly enabled and no real token is configured
        if MAESTRO_DEV_MODE and not token_configured:
            if token:
                session["authenticated"] = True
                return redirect(next_url)
            error = "Enter any token to continue (dev mode)."

        else:
            # Normal mode: must have MAESTRO_TOKEN configured and match exactly
            if not token_configured:
                error = "Dashboard not configured: MAESTRO_TOKEN is missing. Set it in your .env."
            elif token == MAESTRO_TOKEN:
                session["authenticated"] = True
                return redirect(next_url)
            else:
                error = "Invalid token. Try again."

    return render_template(
        "login.html",
        error=error,
        next_url=next_url,
        token_configured=token_configured,
        dev_mode=MAESTRO_DEV_MODE,
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    debug = os.getenv("FLASK_DEBUG", "").strip() == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)