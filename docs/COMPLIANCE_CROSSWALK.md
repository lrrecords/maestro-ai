# Compliance Crosswalk

## Purpose

This document maps repository evidence to three commonly requested frameworks: ISO 27001, SOC 2, and HIPAA.

It is a repository evidence crosswalk, not a certification statement. Status values reflect only what is currently visible in the codebase and documentation.

## Status Legend

- Implemented: Clear repository evidence exists.
- Partial: Some evidence exists, but it is not enough to prove full operational control.
- Missing: No direct repository evidence found.
- Not Applicable: The control does not reasonably apply to the repository scope.

## Shared Evidence Inventory

- [dashboard/app.py](../dashboard/app.py)
- [webhook_server.py](../webhook_server.py)
- [.env.example](../.env.example)
- [requirements.txt](../requirements.txt)
- [Dockerfile](../Dockerfile)
- [Procfile](../Procfile)
- [docs/ACCESS_CONTROL_POLICY.md](ACCESS_CONTROL_POLICY.md)
- [docs/INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md)
- [docs/BACKUP_RECOVERY.md](BACKUP_RECOVERY.md)
- [docs/RETENTION_POLICY.md](RETENTION_POLICY.md)
- [docs/SUPPLIER_SECURITY.md](SUPPLIER_SECURITY.md)
- [docs/DEPLOYMENT_EVIDENCE.md](DEPLOYMENT_EVIDENCE.md)
- [docs/CONTROL_EVIDENCE_CHECKLIST.md](CONTROL_EVIDENCE_CHECKLIST.md)

## ISO 27001 Crosswalk

| Control Area | Status | Evidence | Gap |
|---|---|---|---|
| Access control | Partial | Token auth, webhook secret validation, and archived auth/webhook tests | Add access review cadence and rotation records |
| Asset management | Partial | Environment variables documented in `.env.example` | Add an explicit asset inventory and ownership records |
| Cryptography | Partial | `SECRET_KEY` and secret env vars documented | Add key management and encryption-at-rest evidence |
| Operations security | Partial | Deployment evidence pack, release archive, and backup/recovery evidence | Add logging and monitoring evidence |
| Communications security | Partial | Webhook auth and API auth documented | Add TLS/integration security notes and evidence |
| Supplier relationships | Partial | Supplier security policy, supplier review archive, and external dependency documentation | Add vendor due diligence records outside the repo |
| Incident management | Partial | Incident response policy and incident drill archive | Add recurring drills and corrective-action tracking outside the repo |
| Business continuity | Partial | Backup/recovery policy and restore-test archive | Add periodic restore verification outside the repo |
| Compliance | Partial | Control evidence checklist, deployment evidence pack, and release archive | Add ongoing release-by-release evidence retention outside the repo |

## SOC 2 Crosswalk

| Trust Service Category | Status | Evidence | Gap |
|---|---|---|---|
| Security | Partial | Auth controls, webhook validation, deployment evidence, and archived release evidence | Add access review evidence and ongoing monitoring proof |
| Availability | Partial | Docker/Procfile launch path, backup/recovery policy, and restore archive | Add monitoring evidence and operational runbook proof |
| Confidentiality | Partial | Secret handling, `.env.example`, supplier controls, and retention policy | Add key management and data classification evidence |
| Processing Integrity | Partial | Authenticated workflows, tests, controlled deployment path, and release sign-off | Add repeatable validation evidence outside the repo |
| Privacy | Missing | No repository evidence of a privacy program or data-subject workflow | Define privacy scope, if applicable, before claiming coverage |

## HIPAA Crosswalk

| Safeguard Family | Status | Evidence | Gap |
|---|---|---|---|
| Administrative safeguards | Partial | Access control policy, incident response policy, supplier policy, and release archives | Add workforce training, sanction, and formal risk-management evidence outside the repo |
| Physical safeguards | Not Applicable | No physical hosting or facility control is visible in the repository | Document hosting/provider responsibilities if HIPAA scope is asserted |
| Technical safeguards | Partial | Authenticated dashboard/webhook access, secret handling, and archived auth/webhook tests | Add audit logging, unique-user access controls, and transmission security evidence |
| Security management process | Partial | Risk register, control evidence checklist, and release archive | Add recurring risk analysis and documented remediation tracking outside the repo |
| Breach response | Partial | Incident response policy and incident drill archive | Add HIPAA-specific breach notification workflow if PHI is in scope |

## Consolidated Gaps

The repository now shows a coherent control baseline, but the following are still missing as audit-ready proof:

- A privacy program or HIPAA-specific scope statement, if PHI is actually processed.

## Practical Interpretation

- ISO 27001: the strongest fit for the current documentation set, with release evidence now archived, but still partial until operational records are retained outside the repo.
- SOC 2: the shared control themes exist, with release evidence now archived, but the trust-service categories still need ongoing operational proof and governance artifacts.
- HIPAA: only a partial technical/administrative overlap is visible; HIPAA should not be claimed unless PHI is truly in scope and the required administrative and privacy controls are documented.

## Next Evidence Step

Keep the release archive current and retain operational evidence outside the repository for each future release.

That archive is the bridge from “documented controls” to “audit-ready evidence”.