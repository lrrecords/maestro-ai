# ISO 27001 Risk Register

## Purpose

This register captures the core information-security risks visible from the Maestro AI repository and its documented deployment model.

## Risk Scale

- Likelihood: Low, Medium, High
- Impact: Low, Medium, High
- Treatment: Avoid, Mitigate, Transfer, Accept

## Risks

| ID | Risk | Likelihood | Impact | Treatment | Current Evidence | Follow-Up |
|---|---|---:|---:|---|---|---|
| R-01 | Unauthorized dashboard or API access | Medium | High | Mitigate | Token auth in [dashboard/app.py](../dashboard/app.py) and documented headers in [README.md](../README.md) | Define access review cadence and token rotation policy |
| R-02 | Unauthorized webhook invocation | Medium | High | Mitigate | Secret validation in [webhook_server.py](../webhook_server.py) and tests in [tests/test_webhook_security.py](../tests/test_webhook_security.py) | Add incident response and supplier controls for inbound integrations |
| R-03 | Secret leakage through config or docs | Medium | High | Mitigate | `.env.example` documents secrets and [SECURITY.md](../SECURITY.md) warns against committing secrets | Add evidence for secret storage, rotation, and review |
| R-04 | Loss of operational data | Medium | High | Mitigate | Redis-backed job store and documented workflow persistence in [README.md](../README.md) | Add backup, restore, and retention evidence |
| R-05 | Misconfiguration during deployment | Medium | High | Mitigate | Railway and Docker deployment paths are documented in [README.md](../README.md) and [RELEASES.md](../RELEASES.md) | Document change management and deployment approval records |
| R-06 | Third-party service compromise or outage | Medium | Medium | Mitigate | External dependencies documented in [README.md](../README.md) and `.env.example` | Add supplier security review and shared-responsibility notes |
| R-07 | Inadequate audit evidence for controls | High | High | Mitigate | Deployment evidence pack and control evidence checklist now exist | Archive release-specific review artifacts and keep the checklist current |

## Treatment Notes

- R-01 and R-02 are the most immediately testable risks and should remain covered by automated tests.
- R-03 through R-07 require policy, process, and evidence documentation in addition to code controls.
- R-07 is now partially addressed by the deployment evidence pack, but release-specific archived evidence is still needed.

## Review Cadence

- Review this register on every major release and after any security incident or architecture change.
- Reassess likelihood and impact after controls are added or operational evidence is collected.