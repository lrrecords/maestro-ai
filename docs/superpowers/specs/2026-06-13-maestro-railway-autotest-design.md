# Maestro Railway Automated Test and Debug Loop Design

## Goal
Create a repeatable workflow that can test the live Maestro AI Railway deployment, identify regressions, and generate a structured repair prompt for Copilot or another coding agent. The workflow must support production-readiness checks without weakening the CEO approval model or changing public-action safeguards.

## Problem Statement
Maestro AI already has a web app, a Railway deployment target, and a mixed set of local and live validation scripts. What is missing is a single, reliable path for:

- verifying the live Railway deployment behaves as expected,
- capturing failures in a form that an agent can act on,
- turning those failures into a consistent debug/fix prompt,
- keeping the deployment contract stable so automated checks do not drift.

## Proposed Architecture
Use a three-part loop:

1. **Deployment anchor**
   - Keep one canonical Railway entrypoint.
   - Treat `Procfile -> app.py -> dashboard.app:app` as the deployment contract.
   - Ensure docs and scripts point to the same launch path.

2. **Automated live smoke tests**
   - Add a deterministic test runner that can hit the live Railway URL.
   - Verify unauthenticated redirect behavior, login page rendering, public health endpoints, and any post-auth dashboard surfaces that can be exercised with documented credentials.
   - Record status, visible errors, and response details in a machine-readable report.

3. **Debug prompt generator**
   - Convert the smoke-test report into a structured repair prompt for Copilot.
   - Preserve architectural constraints in the prompt, especially the CEO approval gate for public-facing actions.
   - Keep the output scoped to concrete failures and relevant files.

## Components

### 1. Deployment Contract
Responsibilities:
- provide the single supported start command for Railway,
- avoid ambiguous launch paths,
- keep README and deployment docs aligned with runtime behavior.

Interfaces:
- `Procfile`
- `app.py`
- `dashboard/app.py`

Notes:
- `dashboard/app.py` is the actual Flask application module.
- `app.py` is the root shim used by the current Procfile.
- Any alternate entrypoint should be deprecated or clearly documented as non-deployment code.

### 2. Smoke Test Runner
Responsibilities:
- send HTTP checks against the live Railway deployment,
- verify redirect behavior and login page rendering,
- check public health endpoints where available,
- optionally verify authenticated pages when credentials are available,
- capture errors, status codes, and page-level evidence.

Interfaces:
- input: deployment base URL, optional credential/token source, optional route list,
- output: structured markdown or JSON report.

Suggested checks:
- `/`
- `/login`
- `/platform/api/health`
- any documented dashboard landing page after auth,
- any available status endpoints documented in the repo.

### 3. Debug Prompt Generator
Responsibilities:
- transform test output into a concise repair prompt,
- include observed failures, affected routes, and severity,
- preserve constraints such as CEO approval and public-action gating,
- make the prompt easy to paste into Copilot chat.

Interfaces:
- input: smoke-test report,
- output: Copilot-ready prompt with repair instructions and scope locks.

## Data Flow
1. The test runner receives the Railway base URL and optional credentials.
2. It executes the route checks in a fixed order.
3. It records the observed responses and any failure details.
4. It emits a structured report.
5. The prompt generator consumes the report and produces a targeted repair prompt.
6. A coding agent applies the fixes locally.
7. The smoke runner is re-executed against the live deployment or a staging equivalent.

## Error Handling
- If authentication is unavailable, the runner must report that explicitly instead of guessing credentials.
- If a route cannot be reached, the report must distinguish between redirect, 404, 500, and tooling limitation.
- If the deployment is down, the report should stop at the first fatal infrastructure failure.
- If a check is blocked by missing browser or request capability, the report must say so rather than inferring outcome.
- If the app returns an error page, capture the exact visible message and URL.

## Testing Strategy
Validate the workflow itself with three layers:

1. **Local unit checks**
   - confirm the prompt generator formats report data correctly,
   - confirm route ordering and report schema.

2. **Repository-level checks**
   - verify the canonical deployment entrypoint resolves to the Flask app,
   - ensure docs mention the same Railway launch path.

3. **Live deployment smoke checks**
   - run the route checks against Railway,
   - confirm the report captures both successes and blocked checks.

## Constraints
- Do not weaken or bypass CEO approval for posts, emails, or financial actions.
- Do not add unrelated features while stabilizing the deployment workflow.
- Keep the system repeatable and low-noise so it can be used during future regressions.
- Prefer narrow, deterministic checks over broad exploratory automation.

## Assumptions
- The current canonical launch path should remain `Procfile -> app.py -> dashboard.app:app` unless a later review proves otherwise.
- The first useful live checks are unauthenticated landing, login, and health routes.
- Authenticated checks are only feasible when credentials are documented or provided.

## Open Questions
- Should the smoke runner live as a Python script in `scripts/` or as a test module under `tests/`?
- Should the report format be markdown first, JSON first, or both?
- Is a staging Railway environment available, or should the workflow target production only?

## Acceptance Criteria
- A single documented deployment path is defined and referenced consistently.
- The smoke-test workflow can run against the live deployment and produce a structured report.
- The report can be turned into a repair prompt without manual rewriting.
- The workflow preserves Maestro’s approval-gated action model.
- A future agent can repeat the process with minimal setup.
