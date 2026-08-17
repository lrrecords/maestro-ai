You are a senior Flask/Python engineer fixing the Rascalworks OS repo toward a functional open-core MVP.

Non-negotiable constraints:
- Do not weaken, bypass, or auto-approve CEO approval for public-facing actions.
- Keep fixes limited to the failures in the report.
- Prefer the canonical Railway entrypoint: Procfile -> app.py -> dashboard.app:app.

Use this live smoke report as ground truth:

# RASCALWORKS OS Railway Smoke Report

## Test Summary
- Base URL: https://maestro-ai.up.railway.app
- Tests attempted: 7
- Tests completed: 7

## Critical Blockers
- None observed

## Errors Found
- None observed

## Working Correctly
- Login accepted token and redirected into the app.
- Login page renders successfully.
- Platform health endpoint responds successfully.
- /hub loaded successfully after authentication.
- /agents loaded successfully after authentication.
- /platform redirected to http://maestro-ai.up.railway.app/platform/ after authentication.

## Unable to Test
- Browser console errors cannot be observed with requests-only smoke checks.
- Raw HTML source and hidden client-side secrets cannot be verified from rendered responses alone.

Task:
1. Find the root cause of each blocker or error.
2. Make the smallest safe code change that fixes it.
3. Add or update tests for the touched behavior.
4. Re-run focused verification.

Return a short, actionable fix plan with file paths and validation commands.