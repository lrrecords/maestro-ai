import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # maestro-ai/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from functools import wraps
from flask import Flask, redirect, render_template, session, request, url_for

from platform_ops.web import platform_bp
from live.web import live_bp
from studio.web import studio_bp

# Import the LABEL blueprint (original maestro-ai dashboard) as the one at `/`
try:
    from scripts.web_app import bp as label_bp
except ImportError:
    print("WARNING: Could not import 'label_bp' from scripts/web_app.py. The / dashboard will not be available.")
    from flask import Blueprint
    label_bp = Blueprint("label", __name__)  # Dummy fallback


# --- Path Configuration ---
ROOT = Path(__file__).parent.parent          # maestro-ai/
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"

# --- Flask App Initialization ---
app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR)
)

# --- Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24).hex())
app.secret_key = SECRET_KEY
MAESTRO_TOKEN = os.getenv("MAESTRO_TOKEN")
if not MAESTRO_TOKEN:
    raise ValueError("MAESTRO_TOKEN not set in .env file")

# --- Login Decorator (protects routes) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


# --- Blueprint Registration ---
# Register blueprints
app.register_blueprint(label_bp,   url_prefix="/label")
app.config["LABEL_URL_PREFIX"] = "/label"   # lets templates build API paths
app.register_blueprint(platform_bp, url_prefix="/platform")
app.register_blueprint(live_bp, url_prefix="/live")
app.register_blueprint(studio_bp, url_prefix="/studio")


# --- Routes ---

@app.route("/")
def index():
    """
    Root URL:
      • If NOT authenticated → go to /login (and remember we wanted /)
      • If authenticated     → go to the Hub (/hub) **not** the Label dashboard
    """
    if not session.get("authenticated"):
        # keep ?next=/ so users land on /hub after login
        return redirect(url_for("login_page", next=request.path))
    return redirect(url_for("hub"))

@app.route("/label")
@login_required
def label_root_alias():
    # label.index is the “home” route inside label_bp
    return redirect(url_for("label.index"))

@app.route("/hub")
@login_required  # Protect the hub page
def hub():
    """The main hub page with the 4 department cards."""
    return render_template("hub.html")

@app.route("/login", methods=["GET", "POST"])
def login_page():
    """Login handler. After success, go to the hub page (default)."""
    # If the user came from a protected page, go back there; otherwise go to hub.
    next_url = request.form.get("next") or request.args.get("next", url_for("hub"))
    error = None

    if request.method == "POST":
        token = request.form.get("token", "").strip()
        if token == MAESTRO_TOKEN:
            session["authenticated"] = True
            return redirect(next_url)
        error = "Invalid token. Try again."

    return render_template("login.html", error=error, next_url=next_url)

@app.route("/logout")
def logout():
    """Log out and return to login."""
    session.clear()
    return redirect(url_for("login_page"))


# --- Entry Point ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)