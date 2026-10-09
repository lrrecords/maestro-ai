# Accessibility Audit — Rascalworks OS Public Site

**Unit:** ICTWEB433 — Confirm accessibility of websites for people with special needs
**Standard:** WCAG 2.1 Level AA
**Auditor:** Brett Caporn
**Audit date:** 2026-10-08 (Lighthouse) and 2026-10-09 (axe scans, manual keyboard testing)
**Site / URLs audited:**
- `https://rascalworks.lrrecords.com.au/` (landing.html)
- `https://rascalworks.lrrecords.com.au/login` (login.html)

**Commit audited:** c096cd4 (accessibility remediation)

---

## 1. Scope

| In scope | Out of scope (this audit) |
|---|---|
| Public landing page | Authenticated dashboard (hub.html, dept_*.html) |
| Login page | |

**Scope rationale:** The public pages are the entry point for every user, including people using assistive technology. The authenticated dashboard is an internal operator tool and was not remediated in this round. It is logged as a follow-up under Section 6.

---

## 2. Tools and method

| Tool | Version | Purpose |
|---|---|---|
| Google Lighthouse (Chrome DevTools) | 13.4.1 | Automated accessibility scoring, desktop + mobile emulation |
| axe DevTools (browser extension) | axe-core 4.13.0 | Automated WCAG 2.1 AA rule checks |
| Manual keyboard test | — | Tab order, focus visibility, menu toggle, form operation |
| Chrome DevTools Rendering panel | — | Emulate `prefers-reduced-motion: reduce` |
| Browser zoom | — | 200% zoom / reflow check |
| Screen reader spot check | — | Not performed this round (see Section 6) |

Tests were run against the live production site in a Chromium-based browser on Windows 10/11 (x64).

Automated tools catch only part of all WCAG issues, so manual keyboard testing was done as well (Section 4).

---

## 3. Automated results

### Lighthouse — Accessibility score

| Page | Desktop | Mobile | Audits passed | Not applicable | Flagged for manual check |
|---|---|---|---|---|---|
| Landing | **100 / 100** | **100 / 100** | 27 | 39 | 10 |
| Login | **100 / 100** | **100 / 100** | 23 | 43 | 10 |

Each page and form factor was run at least twice to confirm the results were consistent. Every run scored 100.

| Report file (`docs/audits/`) | Page | Form factor | Score |
|---|---|---|---|
| rascalworks.lrrecords.com.au-20261008T195914.html | Landing | Desktop | 100 |
| rascalworks.lrrecords.com.au-20261008T200334.html | Landing | Desktop | 100 |
| rascalworks.lrrecords.com.au-20261008T200410.html | Landing | Mobile | 100 |
| rascalworks.lrrecords.com.au-20261008T200444.html | Landing | Mobile | 100 |
| rascalworks.lrrecords.com.au-20261008T200525.html | Landing | Mobile | 100 |
| rascalworks.lrrecords.com.au-20261008T200919.html | Login | Mobile | 100 |
| rascalworks.lrrecords.com.au-20261008T201002.html | Login | Mobile | 100 |
| rascalworks.lrrecords.com.au-20261008T201029.html | Login | Desktop | 100 |
| rascalworks.lrrecords.com.au-20261008T201051.html | Login | Desktop | 100 |

Lighthouse flags 10 items on each page as "manual check" because automated tools cannot verify them, such as logical tab order and focus management. They are covered in Section 4.

### axe DevTools — WCAG 2.1 AA, Best Practices off

| Page | Critical | Serious | Moderate | Minor | Total |
|---|---|---|---|---|---|
| Landing | 0 | 0 | 0 | 0 | **0** |
| Login | 0 | 0 | 0 | 0 | **0** |

Both pages returned 0 automatic, guided and manual issues in axe DevTools (axe-core 4.13.0).

Evidence: `docs/audits/axe-landing.png`, `docs/audits/axe-login.png`


---

## 4. Manual checks

Manual testing was done on 2026-10-09: keyboard-only navigation (mouse unused), 200% browser zoom, and reduced-motion emulation via Chrome DevTools. Rows marked "automated" are verified by the Lighthouse and axe results in Section 3, which returned zero failures for those rules.

| Check | WCAG ref | Landing | Login | How verified |
|---|---|---|---|---|
| All interactive elements reachable by Tab | 2.1.1 | ☑ Pass | ☑ Pass | Manual keyboard |
| Logical focus order | 2.4.3 | ☑ Pass | ☑ Pass | Manual keyboard |
| Visible focus indicator | 2.4.7 | ☑ Pass | ☑ Pass | Manual keyboard |
| Menu toggle operable by keyboard, announces expanded state | 4.1.2 | ☑ Pass | n/a | Manual keyboard + automated (aria-expanded) |
| Scrollable terminal region reachable and scrollable by keyboard | 2.1.1 | ☑ Pass | n/a | Manual keyboard |
| Single h1, logical h2→h3 hierarchy | 1.3.1 | ☑ Pass | ☑ Pass | Automated |
| Form inputs have accessible labels | 1.3.1 / 3.3.2 | ☑ Pass | ☑ Pass | Automated |
| Images have meaningful alt / decorative icons hidden | 1.1.1 | ☑ Pass | ☑ Pass | Automated |
| Page language declared | 3.1.1 | ☑ Pass | ☑ Pass | Automated |
| Text contrast ≥ 4.5:1 (3:1 large text) | 1.4.3 | ☑ Pass | ☑ Pass | Automated |
| Animations respect prefers-reduced-motion | 2.3.3 | ☑ Pass | ☑ Pass | Manual: DevTools Rendering emulation `prefers-reduced-motion: reduce` — animations stop/settle. Evidence: `docs/audits/reduced-motion.png` |
| Usable at 200% zoom with no loss of content | 1.4.4 | ☑ Pass | ☑ Pass | Manual: browser zoom 200%, no content cut off or overlapping, menu operable |
| Screen reader announces landmarks and headings correctly | 1.3.1 | — | — | Not performed this round (see Section 6) |

---

## 5. Remediation log

| # | Issue | WCAG ref | Fix | Commit | Re-tested |
|---|---|---|---|---|---|
| 1 | Missing ARIA labels on sections/nav | 4.1.2 | aria-label added | c096cd4 | ☑ Lighthouse 2026-10-08 |
| 2 | Menu toggle state not announced | 4.1.2 | aria-expanded added | c096cd4 | ☑ Lighthouse + keyboard 2026-10-09 |
| 3 | Decorative icons read by screen readers | 1.1.1 | aria-hidden added | c096cd4 | ☑ Lighthouse 2026-10-08 |
| 4 | Form inputs unlabelled | 1.3.1 | sr-only labels | c096cd4 | ☑ Lighthouse 2026-10-08 |
| 5 | Scrollable terminal not keyboard accessible | 2.1.1 | role="region" tabindex="0" | c096cd4 | ☑ Keyboard 2026-10-09 |
| 6 | Heading hierarchy broken | 1.3.1 | h1→h2→h3 restructure | c096cd4 | ☑ Lighthouse 2026-10-08 |
| 7 | No page language | 3.1.1 | lang="en" | c096cd4 | ☑ Lighthouse 2026-10-08 |
| 8 | Motion not reduced on request | 2.3.3 | prefers-reduced-motion | c096cd4 | ☑ DevTools emulation 2026-10-09 |
| 9 | Login page missing h1 / labels | 1.3.1 | h1 + label added | c096cd4 | ☑ Lighthouse 2026-10-08 |

All nine fixes were re-tested and confirmed. No new issues were found during this audit.

---

## 6. Outstanding items and follow-up

- Authenticated dashboard (hub.html, dept_*.html) is not yet audited. Planned for a follow-up audit using the same method.
- Screen reader testing (e.g. NVDA) was not performed in this round. Automated checks confirm the underlying semantics (landmarks, labels, headings, alt text) are present. A screen reader pass is planned alongside the dashboard audit.

---

## 7. Confirmation

I confirm the pages listed in Section 1 were tested against WCAG 2.1 AA using the tools and methods in Section 2. The results above reflect that testing as of the audit date.

**Signed:** Brett Caporn  **Date:** 2026-10-09
