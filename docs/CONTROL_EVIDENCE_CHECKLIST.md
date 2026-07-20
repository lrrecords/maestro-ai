# Control Evidence Checklist

## Purpose

Use this checklist to package evidence for ISO 27001-style review, release sign-off, or external audit preparation.

## Checklist

- [x] Access control policy exists and matches code behavior.
- [x] Dashboard auth headers and login flow are documented.
- [x] Webhook secret validation is documented.
- [x] Secret and environment-variable inventory exists in `.env.example`.
- [x] Deployment path is documented with `Dockerfile` and `Procfile`.
- [x] Incident response policy exists.
- [x] Backup and recovery policy exists.
- [x] Retention policy exists.
- [x] Supplier security policy exists.
- [x] Deployment evidence pack exists.
- [x] Control evidence checklist exists.
- [x] Archive a release-specific deployment approval record.
- [x] Archive a backup restore test result.
- [x] Archive an incident drill result.
- [x] Archive a supplier review/sign-off record.
- [x] Archive auth and webhook test output for the release.

Archived evidence:

- [docs/releases/2026-07-20-release-evidence.md](docs/releases/2026-07-20-release-evidence.md)
- [docs/releases/2026-07-20-deployment-approval.md](docs/releases/2026-07-20-deployment-approval.md)
- [docs/releases/2026-07-20-backup-restore.md](docs/releases/2026-07-20-backup-restore.md)
- [docs/releases/2026-07-20-incident-drill.md](docs/releases/2026-07-20-incident-drill.md)
- [docs/releases/2026-07-20-supplier-review.md](docs/releases/2026-07-20-supplier-review.md)

## Packaging Notes

- Store archived evidence in a release folder or a separate compliance archive.
- Include the release tag, date, owner, and a short summary of what was verified.
- Keep the archived material read-only once a release is closed.

## Review Cadence

- Review this checklist at least once per release.
- Update it immediately after any security incident, restore test, or supplier change.