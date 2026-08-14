# Rascalworks OS on lrrecords.com.au — Rollout Checklist (Lean)

Start Date: [INSERT DATE]  
Target Launch: [INSERT DATE]  
Owner: Brett

---

## Launch Objective

Ship a clear Maestro website presence without overbuilding.

Success =
- Maestro card appears in homepage services section
- Card links to `/maestro`
- `/maestro` explains what Maestro is and is not
- `/maestro` includes GitHub CTA + Contact CTA

---

## Phase 1: Core Launch (Do This First)

### A) Homepage services card
- [ ] Add Maestro card/column to `/#services`
- [ ] Use one approved description from `docs/EASYFUNNELS_PAGE_COPY_TEMPLATES.md`
- [ ] Set button text (See Maestro / How Maestro Works / Visit Maestro Hub)
- [ ] Set button URL to `https://lrrecords.com.au/maestro`
- [ ] Check visual consistency with adjacent service cards

### B) Maestro hub page (`/maestro`)
- [ ] Create page with compact template from `docs/EASYFUNNELS_PAGE_COPY_TEMPLATES.md`
- [ ] Include these sections:
  - [ ] Hero
  - [ ] What it does
  - [ ] What it never does
  - [ ] Proof block
  - [ ] CTA block
- [ ] Add CTA buttons:
  - [ ] View on GitHub -> `https://github.com/lrrecords/maestro-ai`
  - [ ] Contact LRRecords -> `https://lrrecords.com.au/contact`
  - [ ] Read FAQ (optional now) -> `/resources/maestro-faq`

### C) Publish and verify
- [ ] Publish homepage changes
- [ ] Publish `/maestro`
- [ ] Test on desktop + mobile
- [ ] Verify no broken links
- [ ] Confirm copy includes: "Maestro does not generate music or art"

---

## Go-Live Acceptance Criteria

- [ ] Homepage services shows Maestro card
- [ ] Maestro card CTA opens `/maestro`
- [ ] `/maestro` page is public and readable
- [ ] GitHub CTA works from `/maestro`
- [ ] Contact CTA works from `/maestro`
- [ ] Mobile layout is acceptable

If all boxes are checked, launch is complete.

---

## Phase 2: Optional Enhancements (Only After Launch)

### Content/Trust
- [ ] Create `/resources/maestro-faq`
- [ ] Add Maestro mention on About page
- [ ] Add footer link to `/maestro`

### Content Engine
- [ ] Publish "Why We Built Rascalworks OS" blog post
- [ ] Use SCRIBE to automate future Maestro posts
- [ ] Add monthly Maestro update cadence

### Technical Automation
- [ ] Validate EasyFunnels -> Maestro inbound webhooks (CRM/order/appointment)
- [ ] Validate n8n social dispatch from approved actions
- [ ] Add GA4 event tracking for Maestro CTAs

---

## 30-Day Metrics (Simple)

- [ ] `/maestro` page views tracked
- [ ] GitHub CTA clicks tracked (manual or analytics)
- [ ] Contact inquiries mentioning Maestro tracked

Targets (starter):
- 100+ views on `/maestro`
- 20+ GitHub referrals
- 5+ direct inquiries

---

## Rollback / Quick Fix

If anything breaks:
1. Unpublish or draft the broken page section
2. Restore previous services row block
3. Re-publish fixed version

---

## Sign-Off

- [ ] Prepared for launch
- [ ] Published
- [ ] Post-launch checks complete

---

Reference docs:
- `docs/EASYFUNNELS_PAGE_COPY_TEMPLATES.md`
- `docs/EASYFUNNELS_IMPLEMENTATION_GUIDE.md`
- `docs/MAESTRO_MARKETING_PLAN.md`
