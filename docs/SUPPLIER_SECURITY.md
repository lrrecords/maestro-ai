# Supplier Security Policy

## Purpose

This policy defines the minimum security expectations for third-party suppliers used by Rascalworks OS.

## Supplier Scope

- Railway hosting and deployment services.
- LLM providers used for local or cloud inference.
- n8n and webhook-connected automation services.
- EasyFunnels, social media APIs, and other external integrations referenced in the repository.

## Expectations

- Each supplier should have a documented purpose and data-sharing boundary.
- Credentials for suppliers must be stored outside the repository and treated as secrets.
- The project should understand whether the supplier acts as a processor, controller, or infrastructure dependency in practice.
- Supplier outages or compromise must be considered in the risk register and incident response process.

## Review Criteria

- What data is shared with the supplier.
- Whether the supplier supports secure transport and secret handling.
- Whether a contractual or policy basis exists for the relationship, such as terms of service or a BAA where applicable.
- Whether the supplier is required for production, development, or optional workflows.

## Evidence to Retain

- Supplier list and purpose statement.
- Notes on what data each supplier can access.
- Any relevant terms, agreements, or shared-responsibility notes.
- Review record for supplier risk acceptance or mitigation.

## Current Known Suppliers From the Repo

- Railway for hosting the live deployment.
- Anthropic and Ollama for model access.
- n8n for automation and webhook routing.
- EasyFunnels and social APIs for SCRIBE-related publishing workflows.

## Review Cadence

- Review suppliers when they are added, removed, or used in a new way.
- Reassess supplier risk after any security incident or major deployment change.