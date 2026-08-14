# ISO 27001 Scope Statement

## Purpose

This document defines the information security management scope for Rascalworks OS so the repository can be assessed consistently against ISO 27001 controls.

## In Scope

- The Rascalworks OS application source code in this repository.
- The Flask dashboard, API routes, agent orchestration code, and supporting scripts.
- Configuration files and deployment artifacts that affect security posture, including `.env.example`, `Dockerfile`, `Procfile`, and Railway-related deployment notes.
- Documentation that defines security, access, and operational control expectations.
- Hosted deployment operations for the public Railway instance when they rely on repository-managed settings and procedures.

## Out of Scope

- External systems not controlled by this repository, except where their use is documented as a dependency or supplier risk.
- Personal devices, local development machine security, and user-managed third-party accounts outside the project’s control.
- Premium/proprietary code that is not present in the open-core repository unless explicitly referenced as a dependency boundary.

## Interested Parties

- Repository maintainers and contributors.
- Operators of the hosted Railway deployment.
- Internal users who authenticate to the dashboard and API.
- Third-party suppliers such as hosting, LLM, webhook, and automation providers.

## Security Objectives

- Protect dashboard, API, and webhook access using authenticated controls.
- Prevent secret leakage and unauthorized configuration changes.
- Preserve availability and integrity of operational data.
- Maintain evidence that security controls are reviewed and improved over time.

## Scope Notes

- The public hosted instance is part of the operational scope because it uses repository-defined configuration and deployment procedures.
- Development-only shortcuts such as `MAESTRO_DEV_MODE=1` are not part of production scope and must not be used as evidence of production control effectiveness.

## Review Cadence

- Review this scope statement at least once per release or when deployment architecture changes.
- Update it whenever new suppliers, data classes, or production workflows are introduced.