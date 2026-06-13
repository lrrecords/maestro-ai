"""Live Railway smoke checks and debug prompt generation for Maestro AI."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


@dataclass(frozen=True)
class RouteCheck:
    path: str
    method: str = "GET"
    auth_required: bool = False


def default_check_order() -> list[RouteCheck]:
    return [
        RouteCheck("/"),
        RouteCheck("/login"),
        RouteCheck("/platform/api/health"),
        RouteCheck("/hub", auth_required=True),
        RouteCheck("/agents", auth_required=True),
        RouteCheck("/platform", auth_required=True),
    ]


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _shorten(text: str, limit: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _make_request(session: requests.Session, method: str, url: str, timeout: int) -> requests.Response:
    method = method.upper()
    request = getattr(session, method.lower())
    return request(url, allow_redirects=False, timeout=timeout)


def run_live_smoke_checks(
    base_url: str,
    login_token: str | None = None,
    timeout: int = 15,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    session = session or requests.Session()
    base_url = _normalize_base_url(base_url)
    attempts: list[dict[str, Any]] = []
    working: list[str] = []
    blockers: list[str] = []
    unable_to_test: list[str] = [
        "Browser console errors cannot be observed with requests-only smoke checks.",
        "Raw HTML source and hidden client-side secrets cannot be verified from rendered responses alone.",
    ]
    errors: list[dict[str, Any]] = []

    authenticated = False
    if login_token:
        login_url = f"{base_url}/login"
        login_response = session.post(
            login_url,
            data={"token": login_token, "next": "/hub"},
            allow_redirects=False,
            timeout=timeout,
        )
        attempts.append(
            {
                "path": "/login",
                "method": "POST",
                "status_code": login_response.status_code,
                "location": login_response.headers.get("Location"),
                "snippet": _shorten(login_response.text),
            }
        )
        if login_response.status_code in {301, 302, 303, 307, 308}:
            authenticated = True
            working.append("Login accepted token and redirected into the app.")
        elif "invalid" in login_response.text.lower() or "missing" in login_response.text.lower():
            blockers.append("Login token was rejected by the login form.")
            errors.append(
                {
                    "path": "/login",
                    "status_code": login_response.status_code,
                    "detail": _shorten(login_response.text),
                }
            )
        else:
            blockers.append("Login did not produce an authenticated redirect.")

    for check in default_check_order():
        if check.auth_required and not authenticated:
            unable_to_test.append(f"{check.path}: requires documented credentials or a valid login token.")
            continue

        url = f"{base_url}{check.path}"
        response = _make_request(session, check.method, url, timeout)
        location = response.headers.get("Location")
        snippet = _shorten(response.text)
        attempts.append(
            {
                "path": check.path,
                "method": check.method,
                "status_code": response.status_code,
                "location": location,
                "snippet": snippet,
            }
        )

        if check.path == "/" and response.status_code in {301, 302, 303, 307, 308} and location and "/login" in location:
            working.append("Root redirects unauthenticated users to /login.")
        elif check.path == "/login" and response.status_code == 200:
            working.append("Login page renders successfully.")
        elif check.path == "/platform/api/health" and response.status_code == 200:
            working.append("Platform health endpoint responds successfully.")
        elif check.auth_required and response.status_code == 200:
            working.append(f"{check.path} loaded successfully after authentication.")
        elif check.auth_required and response.status_code in {301, 302, 303, 307, 308} and location and "/login" in location:
            blockers.append(f"{check.path} redirected back to login after authentication.")
            errors.append(
                {
                    "path": check.path,
                    "status_code": response.status_code,
                    "detail": f"Redirected to {location}",
                }
            )
        elif check.auth_required and response.status_code in {301, 302, 303, 307, 308} and location:
            working.append(f"{check.path} redirected to {location} after authentication.")
        elif response.status_code >= 500:
            blockers.append(f"{check.path} returned HTTP {response.status_code}.")
            errors.append(
                {
                    "path": check.path,
                    "status_code": response.status_code,
                    "detail": snippet,
                }
            )
        elif response.status_code >= 400:
            errors.append(
                {
                    "path": check.path,
                    "status_code": response.status_code,
                    "detail": snippet,
                }
            )
            if response.status_code == 404:
                blockers.append(f"{check.path} returned 404.")

    report = {
        "base_url": base_url,
        "tests_attempted": len(attempts),
        "tests_completed": len([entry for entry in attempts if entry.get("status_code") is not None]),
        "blockers": blockers,
        "errors": errors,
        "working": working,
        "unable_to_test": unable_to_test,
        "attempts": attempts,
    }
    return report


def format_markdown_report(report: dict[str, Any]) -> str:
    lines = ["# Maestro Railway Smoke Report", "", "## Test Summary"]
    lines.append(f"- Base URL: {report.get('base_url', '')}")
    lines.append(f"- Tests attempted: {report.get('tests_attempted', 0)}")
    lines.append(f"- Tests completed: {report.get('tests_completed', 0)}")

    blockers = report.get("blockers", [])
    lines.extend(["", "## Critical Blockers"])
    if blockers:
        lines.extend([f"- {blocker}" for blocker in blockers])
    else:
        lines.append("- None observed")

    errors = report.get("errors", [])
    lines.extend(["", "## Errors Found"])
    if errors:
        for error in errors:
            path = error.get("path", "unknown")
            status_code = error.get("status_code", "unknown")
            detail = error.get("detail", "")
            lines.append(f"- {path} returned HTTP {status_code}: {detail}")
    else:
        lines.append("- None observed")

    working = report.get("working", [])
    lines.extend(["", "## Working Correctly"])
    if working:
        lines.extend([f"- {item}" for item in working])
    else:
        lines.append("- None observed")

    unable_to_test = report.get("unable_to_test", [])
    lines.extend(["", "## Unable to Test"])
    if unable_to_test:
        lines.extend([f"- {item}" for item in unable_to_test])
    else:
        lines.append("- None")

    return "\n".join(lines)


def build_debug_prompt(report: dict[str, Any]) -> str:
    report_markdown = format_markdown_report(report)
    return (
        "You are a senior Flask/Python engineer fixing the Maestro AI repo toward a functional open-core MVP.\n\n"
        "Non-negotiable constraints:\n"
        "- Do not weaken, bypass, or auto-approve CEO approval for public-facing actions.\n"
        "- Keep fixes limited to the failures in the report.\n"
        "- Prefer the canonical Railway entrypoint: Procfile -> app.py -> dashboard.app:app.\n\n"
        "Use this live smoke report as ground truth:\n\n"
        f"{report_markdown}\n\n"
        "Task:\n"
        "1. Find the root cause of each blocker or error.\n"
        "2. Make the smallest safe code change that fixes it.\n"
        "3. Add or update tests for the touched behavior.\n"
        "4. Re-run focused verification.\n\n"
        "Return a short, actionable fix plan with file paths and validation commands."
    )


def _write_output(path: str | None, content: str) -> None:
    if not path:
        return
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Maestro live Railway smoke checks.")
    parser.add_argument("--base-url", required=True, help="Live Maestro deployment URL.")
    parser.add_argument("--login-token", help="Optional login token for authenticated checks.")
    parser.add_argument("--report-file", help="Write the markdown report to this path.")
    parser.add_argument("--prompt-file", help="Write the debug prompt to this path.")
    parser.add_argument("--json-file", help="Write the raw report JSON to this path.")
    args = parser.parse_args(argv)

    report = run_live_smoke_checks(args.base_url, login_token=args.login_token)
    markdown = format_markdown_report(report)
    prompt = build_debug_prompt(report)

    print(markdown)
    print()
    print("## Copilot Debug Prompt")
    print(prompt)

    _write_output(args.report_file, markdown)
    _write_output(args.prompt_file, prompt)
    if args.json_file:
        Path(args.json_file).write_text(json.dumps(report, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())