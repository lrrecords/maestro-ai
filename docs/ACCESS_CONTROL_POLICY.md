# Access Control Policy

## Purpose

This policy defines the minimum access-control expectations for Maestro AI in a way that can support ISO 27001 evidence collection.

## Policy Statements

1. Access to the dashboard, API, and inbound webhooks must be authenticated.
2. Production secrets must not be committed to the repository.
3. Shared tokens and webhook secrets must be treated as sensitive credentials.
4. Access should follow least-privilege principles and be reviewed regularly.
5. Development-only bypasses must not be treated as production controls.

## Controlled Credentials

- `MAESTRO_TOKEN` for dashboard and API authentication.
- `WEBHOOK_SECRET` for inbound webhook authorization.
- `SECRET_KEY` for session integrity.
- LLM and integration tokens exposed through `.env.example` and deployment environments.

## Access Rules

- All interactive dashboard users must authenticate before reaching protected routes.
- API clients must use either `X-MAESTRO-TOKEN` or `Authorization: Bearer <token>` as documented in the repository.
- Webhook senders must use either `X-WEBHOOK-SECRET` or `Authorization: Bearer <secret>`.
- Development mode bypasses, where present, are limited to local development and must be explicitly disabled in production.

## Joiner / Mover / Leaver Expectations

- Joiners receive credentials through a separate secure channel from application links.
- Movers have credentials and access reviewed when duties or scope change.
- Leavers or revoked users must have access removed or rotated promptly.

## Review and Rotation

- Review production access at least once per release or access change.
- Rotate shared secrets when a credential is exposed, a user leaves, or a deployment scope changes.
- Keep evidence of each review and rotation event in the compliance record.

## Evidence to Retain

- Auth test results from the repository test suite.
- Environment-variable inventory for production and staging.
- Records of credential rotation and authorized access review.
- Deployment approvals or change notes when access-sensitive configuration changes.

## Exceptions

- Any exception to this policy must be documented with owner approval, expiration date, and compensating controls.