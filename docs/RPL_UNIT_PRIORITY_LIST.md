# RPL Unit Priority List - ICT40120

This list ranks the units by how strongly the current evidence supports them, based on the current Rascalworks OS, Artist Pages, public website, GitHub, and documentation pack.

## Highest confidence

1. ICTICT435 - Create technical documentation
- Strong evidence: README files, release notes, setup guides, RPL overview, evidence index, screenshot appendix template.
- Why it is strong: you have extensive written documentation and structured submission artifacts.

2. ICTCLD401 - Configure cloud services
- Strong evidence: Artist Pages / Supabase config, cloud setup notes, deployment guidance, hosted website evidence.
- Why it is strong: clear cloud configuration and service integration artifacts.

3. ICTDBS416 - Create basic relational databases
- Strong evidence: Artist Pages schema and SQL files, short-links table, RLS policies, seed scripts.
- Why it is strong: direct relational schema and SQL implementation evidence.

4. ICTWEB451 - Apply structured query language in relational databases
- Strong evidence: Artist Pages SQL scripts, inserts, upserts, policies, and schema setup.
- Why it is strong: direct SQL usage is explicit and practical.

5. ICTWEB434 - Transfer content to websites
- Strong evidence: live LRRecords site, Maestro docs and updates, public website continuity, GitHub release/repository publishing.
- Why it is strong: you have real ongoing content publishing and maintenance evidence.

6. ICTWEB450 - Evaluate and select a web hosting service
- Strong evidence: deployment docs, Procfile, Dockerfile, Railway notes, hosted site operation.
- Why it is strong: there is practical hosting/deployment selection evidence.

## Medium confidence

7. ICTPRG302 - Apply introductory programming techniques
- Strong evidence: Maestro backend code, tests, agent orchestration, Python/Flask code.
- Why it is medium: the work is stronger than introductory level, but the unit can still be supported by core coding evidence.

8. ICTWEB431 - Create and style simple markup language documents
- Strong evidence: templates, HTML pages, styling assets, public website pages.
- Why it is medium: clear frontend implementation evidence exists, though the unit is relatively basic.

9. ICTWEB432 - Design website layouts
- Strong evidence: Maestro UI templates, LRRecords website pages, Artist Pages public views.
- Why it is medium: layout work is visible, but you should attach screenshots and a short explanation.

10. ICTICT451 - Comply with IP, ethics and privacy policies in ICT environments
- Strong evidence: confidentiality notes, redaction guidance, public/private separation, security sections.
- Why it is medium: this unit often needs a narrative explanation in addition to artifacts.

11. ICTSAS432 - Identify and resolve client ICT problems
- Strong evidence: support-style docs, maintenance notes, troubleshooting examples, user onboarding docs.
- Why it is medium: best supported by examples of problem resolution and support communication.

12. BSBXCS404 - Contribute to cyber security risk management
- Strong evidence: auth headers, webhook secrets, RLS, token handling, redaction practices.
- Why it is medium: you have meaningful controls, but the assessor may want clearer risk-focused commentary.

13. ICTICT443 - Work collaboratively in the ICT industry
- Strong evidence: GitHub activity, releases, documentation, public repo history.
- Why it is medium: collaboration is visible, but a referee letter would help.

14. ICTWEB433 - Confirm accessibility of websites
- Strong evidence: documented WCAG 2.1 AA audit of the public site (`docs/ACCESSIBILITY_AUDIT.md`), remediation commit c096cd4 (ARIA labels, aria-expanded, aria-hidden on decorative icons, sr-only form labels, alt text, keyboard-accessible scroll region, h1→h2→h3 hierarchy, lang="en", prefers-reduced-motion), Lighthouse 13.4.1 reports at 100/100 on landing and login (desktop and mobile), axe DevTools 0 issues on both pages, manual keyboard/zoom/reduced-motion checks (raw evidence in `docs/audits/`).
- Why it is medium: the full confirm-and-remediate cycle is documented for the public site. The audit is scoped to public pages; the authenticated dashboard (hub.html, dept_*.html) and a screen reader pass are logged as follow-ups, so state that scope in the narrative.

15. ICTWEB443 - Implement search engine optimisations
- Strong evidence: public SEO landing page for rascalworks.lrrecords.com.au (commit e0d3599), live site visibility, public content, metadata and publishing practices.
- Why it is medium: explicit SEO implementation work is now in the repo history; reference the commit and live page in the narrative.

## Lower confidence but still supportable

16. ICTAII401 - Identify opportunities to apply artificial intelligence, machine learning and deep learning
- Strong evidence: Rascalworks OS routing, LLM integrations, AI workflow design.
- Why it is lower: this unit may require a clear explanation of how you identified and applied AI opportunities rather than just using AI tools.

17. ICTICT426 - Identify and evaluate emerging technologies and practices
- Strong evidence: multi-provider LLM support, hosting patterns, cloud tooling, platform evolution.
- Why it is lower: you should explain why you chose particular technologies and how you evaluated them.

18. BSBCRT404 - Apply advanced critical thinking to work processes
- Strong evidence: design trade-offs, fallback strategies, architecture notes, release decisions.
- Why it is lower: needs reflective narrative about decisions, alternatives, and trade-offs.

## Evidence gap watchlist

These units may need the most careful wording or extra artifacts:
- ICTPRG302
- ICTICT426
- ICTAII401
- BSBCRT404

ICTWEB443 and ICTWEB433 were removed from this list on 2026-10-09 after the SEO landing page (e0d3599), accessibility remediation (c096cd4) and documented accessibility audit (`docs/ACCESSIBILITY_AUDIT.md`) were added.

## Recommendation

Lead with the strongest units in your narrative and appendix, then use the lower-confidence units only where you can honestly explain the evidence.
- If you can add a referee letter, do it.
- If you can add more screenshots of actual work in production, do it.
- If you can provide a short project timeline for Maestro and Artist Pages, do it.
