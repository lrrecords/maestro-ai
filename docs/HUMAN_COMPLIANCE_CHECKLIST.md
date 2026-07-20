# Human Compliance Checklist

## Purpose

Use this checklist for the work that must be done by a human outside the repository to complete the compliance story for ISO 27001, SOC 2, and HIPAA.

This is not certification evidence by itself. It is the operational follow-through that turns the repository's documented controls into auditable practice.

## Before You Start

- Confirm the current release tag and freeze the evidence set for that release.
- Confirm whether HIPAA is actually in scope. If no PHI is processed, do not claim HIPAA coverage.
- Store the resulting evidence in a separate compliance archive outside the repo.

## ISO 27001 Human Tasks

- [ ] Perform and record a management review for the current release.
- [ ] Perform and record an access review for dashboard, API, and webhook secrets.
- [ ] Record any token or secret rotations.
- [ ] Save a signed or timestamped deployment approval record outside the repo.
- [ ] Run and archive a restore test result for a representative operational data set.
- [ ] Run and archive an incident drill result.
- [ ] Run and archive a supplier review or vendor due-diligence note.
- [ ] Reassess the risk register and note any accepted residual risk.

## SOC 2 Human Tasks

- [ ] Map the current evidence set to Security, Availability, Confidentiality, Processing Integrity, and Privacy.
- [ ] Document control owners and review cadence.
- [ ] Record a change-management or release sign-off step for the current release.
- [ ] Capture monitoring or operational checks that show the controls are used in practice.
- [ ] Archive vendor review notes and any shared-responsibility statements.
- [ ] If privacy is in scope, define the privacy program and retention of any data-subject requests.

## HIPAA Human Tasks

- [ ] Confirm whether PHI is in scope.
- [ ] If PHI is in scope, create a formal HIPAA scope statement.
- [ ] If PHI is in scope, document BAAs or equivalent vendor agreements where required.
- [ ] If PHI is in scope, perform and archive a HIPAA risk analysis.
- [ ] If PHI is in scope, document workforce training and sanctions expectations.
- [ ] If PHI is in scope, document breach-notification steps and contacts.
- [ ] If PHI is in scope, confirm audit logging, unique-user access, and transmission security outside the repo.

## Evidence To Retain

- Release approval record.
- Backup restore proof.
- Incident drill proof.
- Supplier review or vendor due-diligence proof.
- Access review notes.
- Risk review notes.
- Any HIPAA scope decision, if applicable.

## Suggested Cadence

- Repeat this checklist on every major release.
- Repeat access, supplier, and risk reviews at least once per release cycle.
- Repeat restore and incident drills on a recurring schedule you can sustain.
