# Data Retention Policy

## Purpose

This policy defines how Maestro AI handles retention, deletion, and review of operational data.

## Retention Principles

- Keep only the data required to operate, troubleshoot, and audit the system.
- Do not retain secrets in long-lived operational logs.
- Minimize personal or sensitive data in application records wherever possible.
- Use the shortest practical retention period consistent with operational needs and legal obligations.

## Data Classes

- Authentication and access data.
- Operational workflow data.
- Webhook and integration payloads.
- Logs and diagnostic data.
- Documentation and release evidence.

## Retention Expectations

- Sensitive operational data should have a documented retention window.
- Logs should be retained only long enough to support troubleshooting, incident response, and audit evidence.
- Deleted records should be removed or anonymized in a way that matches the data class and operational need.

## Deletion and Legal Hold

- When deletion is requested or required, remove the data from active use and from any backup or archive process where feasible.
- If data must be retained for legal, security, or operational reasons, document the hold and its owner.

## Evidence to Retain

- Retention schedule.
- Deletion or purge records.
- Any exception or legal hold record.
- Review notes showing that retention is still aligned to current operations.

## Review Cadence

- Review retention at least once per release or whenever new data classes are added.