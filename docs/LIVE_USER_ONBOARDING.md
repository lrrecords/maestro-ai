# Maestro AI Live User Onboarding Guide

This guide helps you onboard someone to the live Maestro deployment quickly and safely.

## 1. Before you invite someone

Use this preflight checklist:

- Confirm production is healthy (run smoke checks before demos).
- Confirm the login token is current.
- Confirm the user understands this is an MVP and features may evolve.

Recommended links to share:

- Live app: https://maestro-ai.up.railway.app
- Repository: https://github.com/lrrecords/maestro-ai
- Quickstart (self-host): docs/quickstart.md

## 2. What to send a new user

Send one short onboarding message in this format:

```text
Welcome to Maestro AI.

1) Open: https://maestro-ai.up.railway.app
2) Enter the login token I sent you separately.
3) After login, start at /hub and then open /agents.
4) Run one safe starter workflow (ATLAS or VINYL) to see structured output.

If login fails, tell me immediately and do not keep retrying.
```

Security note:

- Always send the token in a separate message/channel from the app link.
- Rotate the token if it is ever shared in the wrong place.

## 3. Suggested 5-minute guided walkthrough

Use this sequence for first-time users:

1. Login at `/login` and confirm they land on `/hub`.
2. Show departments briefly (Label, Studio, Live, Platform Ops).
3. Open `/agents` and run one low-risk agent.
4. Explain the approval pattern: sensitive actions require explicit approval.
5. Show where outputs appear and how to review result quality.

## 4. First session success criteria

A new user is onboarded successfully when they can:

- Log in without help.
- Reach `/hub` and `/agents`.
- Run at least one agent and understand output basics.
- Name one workflow they want Maestro to automate next.

## 5. Troubleshooting login quickly

If a user cannot log in:

1. Re-send token exactly (no extra spaces or quotes).
2. Ask them to paste, not type manually.
3. Verify they are on the correct URL.
4. Re-test with a known-good token.
5. If still failing, run smoke test with authenticated checks.

## 6. Operator checklist after onboarding call

- Capture user feedback and requested automations.
- Add one follow-up action to roadmap/backlog.
- Confirm next check-in date.

## 7. Token rotation (shared login model)

Maestro currently uses one shared app login token (`MAESTRO_TOKEN`) for hosted access.

When to rotate:

- A token was shared in the wrong place.
- A user leaves your pilot group.
- You want to regularly refresh access.

### Local/self-host rotation

1. Update `MAESTRO_TOKEN` in your `.env`.
2. Restart the app.
3. Send the new token to current approved users only.

### Railway rotation

1. Open Railway project environment variables.
2. Set a new value for `MAESTRO_TOKEN`.
3. Redeploy/restart service.
4. Verify login with the new token.
5. Re-share token via a separate secure channel.

Optional helper scripts:

- `scripts/set_railway_env_vars.ps1`
- `scripts/set_railway_env_vars.sh`

---

For local/self-host onboarding, use docs/quickstart.md.
