# Maestro AI Evals

This directory contains offline evaluation assets for Maestro AI agents.

## Goal

Improve confidence in agent behavior without changing the production runtime.

These evals are designed to help catch regressions in:
- output schema
- domain compliance
- approval-boundary behavior
- content quality
- provider-to-provider differences

## Scope

This eval harness is currently focused on:
- SCRIBE
  - method: `propose_topics`

Future candidates may include:
- ATLAS
- BOOK
- TOUR

## Principles

- No production dependency: evals do not affect Flask app startup, routing, or deployment.
- Sidecar only: eval code lives under `evals/` and calls existing Maestro agent code through thin runners.
- Small, curated fixtures first: start with a stable hand-written eval set before expanding.
- Deterministic checks before judge models: schema and policy checks should run before LLM-based scoring.

## Layout

- `fixtures/` — eval inputs and schemas
- `runners/` — scripts that invoke existing Maestro agent methods
- `judges/` — scoring and rule-based evaluation logic
- `results/` — generated eval artifacts

## Current SCRIBE coverage

SCRIBE evals currently target `propose_topics()` and test:
- allowed topic domains
- forbidden topic domains
- normalization to `blogTopics`
- expected topic count
- refusal behavior for out-of-scope prompts

## Example workflow

1. Load a fixture from `fixtures/scribe/propose_topics/`
2. Run `ScribeAgent.propose_topics(...)`
3. Save raw and normalized output
4. Validate output schema
5. Score for:
   - domain compliance
   - refusal compliance
   - music-industry relevance
   - approval-boundary safety

## Non-goals

These evals do not currently attempt to test:
- dashboard UI behavior
- webhook delivery
- Redis/network reliability
- full end-to-end multi-agent orchestration
- production deployment behavior
