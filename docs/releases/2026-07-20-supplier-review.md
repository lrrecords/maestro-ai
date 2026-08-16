# Supplier Review and Sign-Off - 2026-07-20

## Purpose

This record captures the supplier review for the Rascalworks OS repository and its documented third-party dependencies.

## Suppliers Reviewed

- Railway hosting and deployment services
- Anthropic and Ollama for model access
- n8n for automation and webhook routing
- EasyFunnels and social APIs for SCRIBE-related publishing workflows

## Review Criteria

- Documented purpose and data-sharing boundary
- Secret handling expectations
- Whether the supplier is required for production, development, or optional workflows
- Shared-responsibility or contractual notes where applicable

## Review Outcome

- Supplier scope is documented in [docs/SUPPLIER_SECURITY.md](../SUPPLIER_SECURITY.md).
- The repository distinguishes core runtime dependencies from optional integrations.
- Supplier risk remains partial because contractual evidence and vendor due-diligence records are not stored in the repository.

## Risk Acceptance

- Status: Pending explicit operational review outside the repository
- Notes: The repository documentation is sufficient to identify suppliers and their intended use, but it does not replace vendor security review or contract management.

## Sign-Off

- Reviewed by: ____________________
- Date: ____________________
- Decision: ____________________
- Notes: ____________________

## Follow-Up Records To Retain

- Supplier list and purpose statement
- Notes on what data each supplier can access
- Any relevant terms, agreements, or shared-responsibility notes
- Review record for supplier risk acceptance or mitigation
