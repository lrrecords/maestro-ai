# Release Evidence Archive - 2026-07-20

## Purpose

This archive captures the release-specific proof currently available in the repository for the Rascalworks OS compliance crosswalk.

## Verification Environment

- Workspace: `c:\Users\brett\Documents\maestro-ai`
- Interpreter: project virtual environment (`venv`)
- Date: 2026-07-20

## Verified Test Evidence

Command:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned; .\venv\Scripts\Activate.ps1; python -m pytest tests/test_webhook_security.py tests/test_smoke_endpoints.py tests/test_permissions_api.py -q
```

Result:

```text
...............................................................          [100%]
63 passed in 16.01s
```

## Evidence Scope

This archive currently covers:

- Auth-protected route behavior
- Webhook secret validation
- Permissions-related route checks

## Remaining Release Evidence To Capture

- Deployment approval record
- Backup restore test output
- Incident drill output
- Supplier review/sign-off record

## Notes

- The first test attempt used the system Python and failed during collection because the environment did not match the project venv.
- The second run used the project venv and passed cleanly.
- Keep this file read-only once the release archive is closed.