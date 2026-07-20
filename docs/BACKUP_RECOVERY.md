# Backup and Recovery Policy

## Purpose

This policy defines how Maestro AI preserves and restores operational data relevant to availability and integrity.

## Backup Scope

- Repository-managed configuration and documentation.
- Operational data directories referenced by the application and workflows.
- State that supports the hosted deployment, where the project controls the configuration or storage.

## Recovery Objectives

- RPO: Restore to the most recent known-good backup available for the affected data set.
- RTO: Restore service as quickly as practical while preserving integrity and approval controls.

## Backup Expectations

- Backups should be automated where feasible.
- Backups must be stored in a location separate from the primary runtime.
- Backup jobs must be monitored for success or failure.
- Restore procedures should be documented before an incident occurs.

## Restore Testing

- Perform a restore test at least once per release cycle or after material storage changes.
- Verify that restored data can support the dashboard, API, and operational workflows.
- Record what was restored, when it was restored, and who validated the result.

## Evidence to Retain

- Backup job configuration.
- Restore test result.
- RPO/RTO decision or target.
- Any backup failure and its resolution.

## Operational Notes

- Hosted deployment data and self-hosted deployment data should be treated separately if their storage models differ.
- If a data set is intentionally transient, document that decision explicitly so it is not assumed to be protected by a backup process it does not use.