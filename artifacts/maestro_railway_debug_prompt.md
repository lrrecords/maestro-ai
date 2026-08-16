You are a senior Flask/Python engineer fixing the Rascalworks OS repo toward a functional open-core MVP.

Non-negotiable constraints:
- Do not weaken, bypass, or auto-approve CEO approval for public-facing actions.
- Keep fixes limited to the failures in the report.
- Prefer the canonical Railway entrypoint: Procfile -> app.py -> dashboard.app:app.

Use this live smoke report as ground truth:

# Maestro Railway Smoke Report

## Test Summary
- Base URL: https://maestro-ai.up.railway.app
- Tests attempted: 3
- Tests completed: 3

## Critical Blockers
- None observed

## Errors Found
- None observed

## Working Correctly
- Root redirects unauthenticated users to /login.
- Login page renders successfully.

## Unable to Test
- Browser console errors cannot be observed with requests-only smoke checks.
- Raw HTML source and hidden client-side secrets cannot be verified from rendered responses alone.
- /hub: requires documented credentials or a valid login token.
- /agents: requires documented credentials or a valid login token.
- /platform: requires documented credentials or a valid login token.

Task:
1. Find the root cause of each blocker or error.
2. Make the smallest safe code change that fixes it.
3. Add or update tests for the touched behavior.
4. Re-run focused verification.

Return a short, actionable fix plan with file paths and validation commands.