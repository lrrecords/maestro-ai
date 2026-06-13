from scripts.maestro_railway_smoke import (
    build_debug_prompt,
    default_check_order,
    format_markdown_report,
    run_live_smoke_checks,
)


def test_default_check_order_covers_core_routes():
    routes = [check.path for check in default_check_order()]

    assert routes[:3] == ["/", "/login", "/platform/api/health"]
    assert "/hub" in routes


def test_format_markdown_report_includes_key_sections():
    report = {
        "base_url": "https://maestro-ai.up.railway.app",
        "tests_attempted": 3,
        "tests_completed": 2,
        "blockers": ["Cannot reach dashboard without auth"],
        "errors": [
            {
                "path": "/login",
                "status_code": 200,
                "detail": "Login page loaded",
            }
        ],
        "working": ["Root redirects to /login"],
        "unable_to_test": ["Dashboard requires credentials"],
    }

    markdown = format_markdown_report(report)

    assert "## Test Summary" in markdown
    assert "Cannot reach dashboard without auth" in markdown
    assert "/login" in markdown
    assert "## Unable to Test" in markdown


def test_build_debug_prompt_preserves_approval_gate():
    report = {
        "base_url": "https://maestro-ai.up.railway.app",
        "blockers": ["Login form does not accept token"],
        "errors": [],
        "working": ["Root redirects to /login"],
        "unable_to_test": ["Dashboard auth blocked"],
    }

    prompt = build_debug_prompt(report)

    assert "CEO approval" in prompt
    assert "Login form does not accept token" in prompt
    assert "Root redirects to /login" in prompt


class _FakeResponse:
    def __init__(self, status_code, text="", location=None):
        self.status_code = status_code
        self.text = text
        self.headers = {}
        if location:
            self.headers["Location"] = location


class _FakeSession:
    def post(self, url, data=None, allow_redirects=False, timeout=None):
        if url.endswith("/login") and data == {"token": "demo-token", "next": "/hub"}:
            return _FakeResponse(302, "", "/hub")
        return _FakeResponse(200, "Invalid token")

    def get(self, url, allow_redirects=False, timeout=None):
        if url.endswith("/"):
            return _FakeResponse(302, "", "/login")
        if url.endswith("/login"):
            return _FakeResponse(200, "MAESTRO AI Access Token")
        if url.endswith("/platform/api/health"):
            return _FakeResponse(200, '{"status":"ok"}')
        if url.endswith("/hub"):
            return _FakeResponse(200, "Hub loaded")
        if url.endswith("/agents"):
            return _FakeResponse(200, "Agents loaded")
        if url.endswith("/platform"):
            return _FakeResponse(308, "", "/platform/")
        return _FakeResponse(404, "Not Found")


def test_run_live_smoke_checks_records_auth_and_public_checks():
    report = run_live_smoke_checks(
        "https://maestro-ai.up.railway.app/",
        login_token="demo-token",
        session=_FakeSession(),
    )

    assert report["tests_attempted"] == 7
    assert any("redirected into the app" in item for item in report["working"])
    assert any("Login page renders successfully" in item for item in report["working"])
    assert any("/hub loaded successfully" in item for item in report["working"])
    assert any("/agents loaded successfully" in item for item in report["working"])
    assert any("/platform redirected to /platform/ after authentication." == item for item in report["working"])
    assert any(entry["path"] == "/hub" for entry in report["attempts"])