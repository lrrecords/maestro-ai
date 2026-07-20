# Deployment Evidence Pack

## Purpose

This document captures the current repository evidence for deployment and operational control. It is intended to support ISO 27001-style review without overstating compliance.

## Evidence Summary

| Area | Evidence | Notes |
|---|---|---|
| Startup path | [dashboard/app.py](../dashboard/app.py), [Dockerfile](../Dockerfile), [Procfile](../Procfile) | The app loads `.env`, honors `PORT`, and launches with `gunicorn` in container/Procfile paths. |
| Access control | [dashboard/app.py](../dashboard/app.py), [docs/ACCESS_CONTROL_POLICY.md](ACCESS_CONTROL_POLICY.md) | Dashboard login is token-based and the policy defines review/rotation expectations. |
| Webhook protection | [webhook_server.py](../webhook_server.py) | Inbound webhooks require `WEBHOOK_SECRET` via header or bearer token. |
| Configuration inventory | [.env.example](../.env.example) | Mandatory secrets and optional integration settings are documented. |
| Dependency baseline | [requirements.txt](../requirements.txt) | Production runtime packages and `gunicorn` are declared. |
| Incident handling | [docs/INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) | Security event triage, containment, and review process are documented. |
| Backup and recovery | [docs/BACKUP_RECOVERY.md](BACKUP_RECOVERY.md) | Backup scope, restore testing, and retention of recovery evidence are documented. |
| Retention | [docs/RETENTION_POLICY.md](RETENTION_POLICY.md) | Data retention and deletion expectations are documented. |
| Supplier review | [docs/SUPPLIER_SECURITY.md](SUPPLIER_SECURITY.md) | Third-party services and review criteria are documented. |

## What This Proves

- The repository now contains a complete paper trail for the main operational controls.
- The codebase shows concrete authentication, webhook, and deployment wiring.
- The project can now be reviewed as an evidence-backed system instead of a documentation-only claim.

## Remaining Operational Gaps

- No archived restore-test output is stored yet.
- No incident drill record is stored yet.
- No supplier review sign-off record is stored yet.
- No release-by-release evidence archive exists yet outside the repo.

## Recommended Evidence Artifacts To Archive

- Latest production deployment approval.
- Backup restore test result.
- Incident drill log.
- Supplier review sign-off.
- Auth and webhook test output for each release.