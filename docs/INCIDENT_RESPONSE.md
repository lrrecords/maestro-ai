# Incident Response Policy

## Purpose

This policy defines how Rascalworks OS should detect, triage, respond to, and document security incidents.

## Incident Types

- Unauthorized dashboard, API, or webhook access.
- Secret exposure or suspected credential compromise.
- Data loss, corruption, or unexpected deletion.
- Deployment compromise or suspicious infrastructure change.
- Third-party service outage that affects confidentiality, integrity, or availability.

## Severity Levels

- Low: Minor issue with no evidence of data exposure or service loss.
- Medium: Limited security or availability impact requiring same-day review.
- High: Confirmed security event affecting production access, data, or availability.
- Critical: Active compromise, broad unauthorized access, or major data loss.

## Response Steps

1. Detect and confirm the event.
2. Triage severity and assign an owner.
3. Contain the impact by disabling affected credentials, routes, or deployments.
4. Preserve evidence such as logs, config snapshots, and timestamps.
5. Eradicate the root cause.
6. Recover service in a controlled way.
7. Perform a post-incident review and record corrective actions.

## Escalation

- Incidents involving production credentials, hosted deployments, or customer-facing data are treated as at least High severity.
- Any suspected breach should be escalated to the project owner and security contact immediately.
- When external suppliers are involved, follow their incident-reporting process in parallel.

## Evidence to Retain

- Incident timeline.
- Triage notes and severity decision.
- Containment and recovery actions.
- Root-cause summary.
- Corrective actions and follow-up owner.

## Communication

- Keep internal updates factual and time-stamped.
- Do not share secrets, tokens, or sensitive logs in public channels.
- Use a separate secure channel for any externally shared remediation details.

## Review Cadence

- Review this policy after any security incident and at least once per release cycle.