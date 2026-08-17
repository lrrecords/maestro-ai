# Rascalworks OS on lrrecords.com.au — EasyFunnels Implementation Guide (Lean)

Date: July 2026  
Status: Launch-first  
Owner: Brett (LRRecords)

---

## Goal

Launch RASCALWORKS OS on the LRRecords website with the smallest setup that still feels professional and clear.

Default approach:
1. Add RASCALWORKS OS as a services card on the homepage.
2. Link that card to `/RASCALWORKS OS`.
3. Use `/RASCALWORKS OS` as the trust page with two CTA paths:
- Artists/managers: FAQ or contact
- Developers/technical teams: GitHub

This keeps the story simple: RASCALWORKS OS is how LRRecords runs operations, not a separate product funnel.

---

## Lean Architecture (Recommended)

### Primary path
- Home services section -> RASCALWORKS OS card -> `/RASCALWORKS OS`

### Secondary path
- `/RASCALWORKS OS` -> GitHub repository

### Optional support page
- `/resources/maestro-faq`

### Why this structure works
- Non-technical visitors get clarity first.
- Technical visitors can still access code quickly.
- Low maintenance burden and fast go-live.

---

## What to Create (Minimum Viable Website Update)

### 1) Homepage services card
Add one RASCALWORKS OS column/card in the services section.

Use copy from:
- `docs/EASYFUNNELS_PAGE_COPY_TEMPLATES.md` (Section "0. LEAN LAUNCH VERSION")

Required settings:
- Button URL: `https://lrrecords.com.au/RASCALWORKS OS`
- Button text: choose one of:
  - See RASCALWORKS OS
  - How RASCALWORKS OS Works
  - Visit RASCALWORKS OS Hub

### 2) RASCALWORKS OS hub page (`/RASCALWORKS OS`)
Create one compact page using:
- `docs/EASYFUNNELS_PAGE_COPY_TEMPLATES.md` (Section "0A. COMPACT RASCALWORKS OS HUB PAGE")

Required sections:
- Hero
- What it does
- What it never does
- Proof block
- CTA block

Required CTAs:
- View on GitHub -> `https://github.com/lrrecords/maestro-ai`
- Contact LRRecords -> `https://lrrecords.com.au/contact`

### 3) Optional FAQ page (`/resources/maestro-faq`)
If you want artist reassurance now, create this page immediately.
If not, add it in week 2.

Copy source:
- `docs/EASYFUNNELS_PAGE_COPY_TEMPLATES.md` (Section "3. ARTIST FAQ PAGE")

---

## GitHub Landing Page Placement

Use GitHub as a secondary destination, not the primary services CTA.

Reason:
- Homepage traffic is mixed (artists, local clients, general visitors).
- Most visitors need plain-language trust and context before technical docs.
- `/RASCALWORKS OS` does the framing; GitHub does technical depth.

Recommended pattern:
- Home card -> `/RASCALWORKS OS`
- `/RASCALWORKS OS` CTA -> GitHub

---

## 60-Minute Launch Runbook

1. Add RASCALWORKS OS card in homepage services section (10-15 min).
2. Create and publish `/RASCALWORKS OS` using compact template (20-30 min).
3. Add GitHub + Contact CTA buttons (5 min).
4. Verify mobile layout and links (10 min).

Done.

---

## Quality Checks Before Publish

- RASCALWORKS OS card appears with consistent spacing/style in services row.
- Card CTA opens `/RASCALWORKS OS`.
- `/RASCALWORKS OS` clearly states "does not generate music or art".
- GitHub CTA works.
- Contact CTA works.
- Page looks clean on mobile.

---

## Optional Add-Ons (Phase 2, Only If Needed)

Add these later, not before launch:
- Dedicated `/RASCALWORKS OS/agents` page
- Blog automation via SCRIBE + n8n
- EasyFunnels inbound webhooks (CRM/order/appointment)
- GA4 event tracking by CTA
- Social dispatch automation from approval queue

These are valuable, but not required for the initial website rollout.

---

## Source Files

- Website copy templates: `docs/EASYFUNNELS_PAGE_COPY_TEMPLATES.md`
- Lean rollout checklist: `docs/MAESTRO_EASYFUNNELS_ROLLOUT_CHECKLIST.md`
- Full marketing plan: `docs/MAESTRO_MARKETING_PLAN.md`

---

The shortest path to live is now the default: one card, one hub page, one clear GitHub path.
