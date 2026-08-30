# Follow-up tickets — Only Institute Review of Rascalworks OS

Source: "Only Institute Review of Rascalworks OS" (Grigori Korotkikh / Only
Institute, presented to Brett Caporn, 31 Aug 2026).

The mechanical, contained fixes from that review shipped in
`claude/only-institute-review-fixes` (temperature/seed determinism, native
system-prompt passthrough, the ScribeAgent inheritance bug, a call-level
audit log, opt-in `parse_json` schema validation, the committed `.venv` +
`.gitignore` gap, and dependency pinning + a lockfile). The items below are
the ones that are genuinely multi-day feature work, not bug fixes — each
needs a real design decision, not just code. Filing them here rather than
half-implementing them.

## 1. Grounding / RAG for SCRIBE content (Hallucination risk — High)

**Review finding:** SCRIBE writes 800–1200 word blog posts entirely from
the model's parametric memory — no fact-checking against any knowledge
base, so gear specs, industry facts, and technical advice can be
fabricated with nothing to catch it.

**Why it's not a quick fix:** needs a real content source (a curated gear
spec sheet? a set of vetted reference docs? web search with citation
requirements?), a retrieval step wired into `propose_topics` /
`generate_blog_versions`, and a policy for what happens when a claim can't
be grounded (refuse the sentence? flag it for CEO review? cite "unverified"
inline?).

**Suggested first step:** narrower than full RAG — add a
"claims extraction" pass after `generate_blog_versions` that pulls out
factual assertions (prices, specs, named products/companies) into a
checklist SCRIBE's human approver sees in the approval-queue UI, so at
least verification effort is targeted instead of "read the whole post
looking for something wrong."

## 2. Eval coverage for the other 24+ agents (Evaluation gaps — Medium)

**Review finding:** `evals/` has a good structure (fixtures, runners,
judges, results) but only covers SCRIBE's `propose_topics()`. BOOK, ROUTE,
SETTLE, MERCH, SAGE, FOCUS, and the rest have zero coverage, and evals
don't run in CI (`ci.yml` currently only runs `pytest tests/` +
`test_agents.py`, confirmed by reading `.github/workflows/ci.yml`).

**Suggested approach:**
- Pick the 2-3 highest-blast-radius agents first (whichever touch money —
  SETTLE — or go out publicly without human review first).
- Reuse the existing `evals/runners` + `evals/judges/scribe_rules.py`
  pattern rather than inventing a new eval framework.
- Wire `evals/` into `ci.yml` as a separate job (not blocking merge
  initially — evals against a live LLM are flaky/slow/costly for every
  push — maybe nightly or on-demand via workflow_dispatch).

## 3. Per-user auth, replacing the single shared MAESTRO_TOKEN (Security — High)

**Review finding:** `MAESTRO_TOKEN` is one token for all API access — no
per-user identity, no rotation, no revocation. If it leaks, everyone's
locked out until you rotate it, and there's no way to tell who did what.

**Why it's not a quick fix:** this is an auth model change, not a bug —
needs a decision on whether to build real per-user tokens (a users table,
issuance/revocation flow) or lean on an existing IdP (the app already has
session login for browser users — could API access piggyback on that with
per-user API keys instead of a second parallel auth system?). Touches every
route currently gated on `X-MAESTRO-TOKEN`.

**Suggested first step:** at minimum, support *multiple* valid tokens (one
per integration/person) via env var or a small tokens table, so a leak or
an offboarding doesn't require rotating the one token every other
integration also depends on. Real per-user auth as a separate, bigger
ticket.

## 4. Webhook secret rotation (Security — High, smaller than #3)

**Review finding:** `WEBHOOK_SECRET` is a single static value with no
rotation mechanism.

**Suggested approach:** support two active secrets at once (current +
next) during a rotation window, same pattern as most webhook providers —
accept either, log which one was used, retire the old one after a grace
period. Much smaller than the auth overhaul in #3; could be picked up
independently.

## 5. Runtime schema validation before persisting agent outputs (Code quality / Evaluation gaps)

**Review finding:** no runtime validation that agent outputs conform to
expected schemas, domain restrictions, or quality thresholds before
they're persisted to the job store.

**Relationship to what already shipped:** `BaseAgent.parse_json()` now
accepts an optional `required_keys` param (see the agents/base_agent
commit) — that's the mechanism, but it's opt-in and only enforces "these
keys exist," not full schema/type/domain validation. This ticket is about
actually wiring it into each agent's call sites with a real per-agent
schema, and deciding what happens on validation failure (retry the LLM
call once? route to CEO review instead of auto-publish? reject and log?).

## 6. Prompt-injection / adversarial input defenses (Security — High)

**Review finding:** no input sanitization or prompt-injection defenses
(DGV test card TC-012). System prompts like SCRIBE's domain restrictions
are enforced only by the model choosing to follow them.

**Why it's not a quick fix:** there's no purely mechanical fix here —
options range from cheap (a second LLM call that classifies "did this
output violate the domain restriction?" before publish) to expensive
(a dedicated guardrails library/service). Needs a decision on acceptable
false-positive rate (SCRIBE occasionally refusing a legitimate topic) vs.
false-negative rate (letting something through), which is a product
call, not just an engineering one.

**Suggested first step:** since content already flows through a CEO
approval queue before publishing, this may be lower urgency than it looks
— the human-in-the-loop step is itself a mitigation. Worth explicitly
deciding whether that's considered sufficient for now, or whether an
automated check is wanted in addition.
