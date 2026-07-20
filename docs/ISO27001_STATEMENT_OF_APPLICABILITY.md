# ISO 27001 Statement of Applicability

## Purpose

This Statement of Applicability maps relevant Annex A controls to the current open-core Maestro AI repository state.

## Status Legend

- Implemented: The repository contains clear evidence of the control.
- Partial: The repository shows some evidence, but not enough to prove full operation.
- Missing: No direct evidence found in the repository.

## Applicability Summary

| Control Area | Status | Evidence | Gap |
|---|---|---|---|
| Access control | Partial | Token auth and webhook secret validation | Add joiner/mover/leaver, review cadence, and token rotation |
| Asset management | Partial | Environment variables documented in `.env.example` | Add asset inventory and ownership |
| Cryptography | Partial | `SECRET_KEY` and secret env vars documented | Add encryption-at-rest and key management evidence |
| Physical security | Missing | None in repo scope | Document supplier/hosting physical responsibility boundaries |
| Operations security | Partial | Hosted deployment, smoke test docs, and backup/recovery policy | Add logging and monitoring evidence |
| Communications security | Partial | Webhook auth and API auth documented | Add transport/TLS and integration security notes |
| System acquisition, development, and maintenance | Partial | Tests and release docs exist | Add secure SDLC and change-management evidence |
| Supplier relationships | Partial | External services referenced in docs and env template | Add supplier risk review and due diligence notes |
| Incident management | Partial | Incident response policy now exists | Add incident drills, logs, and review evidence |
| Business continuity | Partial | Backup/recovery policy now exists | Add restore tests and recovery evidence |
| Compliance | Partial | Control evidence checklist and deployment evidence pack now exist | Add archived release evidence and review notes |

## Not Yet Applicable / Deferred for Open-Core Repo Review

- HR-managed controls that are not visible in the repository, such as employee screening or disciplinary workflows.
- Building-physical-security controls outside the project’s administrative reach.

## Control Notes

- This document is intentionally conservative: if evidence is absent, the control remains partial or missing.
- The goal is not to claim compliance prematurely, but to identify the smallest set of artifacts required to close the gap.

## Next Review

- Update the applicability status after access-control, incident-response, backup/recovery, supplier evidence, and release archives are in place.
- Align this document with any future SOC 2 or HIPAA control mapping so the evidence set can be reused.