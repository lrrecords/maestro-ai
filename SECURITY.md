# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in RASCALWORKS OS, please **do not** open a public GitHub issue.

Instead, report it privately:

- Email: security@lrrecords.com.au (preferred)
- Or: email brett@lrrecords.com.au if the security address isn’t available

Please include:
- A clear description of the issue and potential impact
- Steps to reproduce (proof-of-concept if possible)
- Any relevant logs, screenshots, or code pointers

## Scope / Notes

RASCALWORKS OS is a self-hosted app intended to run locally or in your own infrastructure.

**Never commit secrets** (API keys, tokens, passwords) to this repository.
Use `.env` (see `.env.example`) and keep your `.env` out of git.

## Governance Docs

For formal ISO 27001 working documents, see:

- [docs/ISO27001_SCOPE.md](docs/ISO27001_SCOPE.md)
- [docs/ISO27001_RISK_REGISTER.md](docs/ISO27001_RISK_REGISTER.md)
- [docs/ISO27001_STATEMENT_OF_APPLICABILITY.md](docs/ISO27001_STATEMENT_OF_APPLICABILITY.md)
- [docs/ACCESS_CONTROL_POLICY.md](docs/ACCESS_CONTROL_POLICY.md)
- [docs/INCIDENT_RESPONSE.md](docs/INCIDENT_RESPONSE.md)
- [docs/BACKUP_RECOVERY.md](docs/BACKUP_RECOVERY.md)
- [docs/RETENTION_POLICY.md](docs/RETENTION_POLICY.md)
- [docs/SUPPLIER_SECURITY.md](docs/SUPPLIER_SECURITY.md)
- [docs/COMPLIANCE_CROSSWALK.md](docs/COMPLIANCE_CROSSWALK.md)