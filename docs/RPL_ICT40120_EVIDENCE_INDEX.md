# RPL Evidence Index - ICT40120 (Web Development)

## Candidate and Project

Candidate: [Add your name]  
Qualification: ICT40120 Certificate IV in Information Technology (Web Development)  
Primary Project: Maestro AI  
Repository: https://github.com/lrrecords/maestro-ai

This index is designed to be submitted with the RPL package and used as a checklist during assessor review.

---

## 1. Core Repository Evidence Map

| Evidence Area | Files / Locations | What It Demonstrates |
|---|---|---|
| Application entry and route wiring | `dashboard/app.py` | Flask app setup, blueprints, sessions, auth flow, limiter, OpenAPI exposure |
| Agent architecture | `core/base_agent.py` | OOP structure, reusable methods, LLM handling, persistence patterns |
| LLM provider abstraction | `core/llm_client.py` | Provider-agnostic API integration and environment-driven configuration |
| Job persistence | `core/job_store.py` | Redis integration, fallback strategy, state handling |
| Frontend templates | `templates/hub.html`, `templates/agents_list.html`, `templates/dept_live.html`, `templates/dept_studio.html` | Website layout and interaction design |
| Frontend assets | `dashboard/static/js/`, `dashboard/static/css/` | Client-side behavior, rendering, UX flows |
| Setup and onboarding | `README.md`, `docs/quickstart.md`, `docs/LIVE_USER_ONBOARDING.md` | Installation, operation, troubleshooting, user support |
| Provider setup matrix | `docs/LLM_PROVIDER_SETUP_MATRIX.md` | Configuration documentation quality and deployment flexibility |
| Release management | `RELEASES.md` | Change tracking, maintenance maturity, release communication |
| Test evidence | `tests/test_llm_client.py`, `tests/` | Automated verification, regression checks, deterministic test practice |

---

## 2. Unit-to-Evidence Mapping (Practical)

| Unit | Primary Evidence | Secondary Evidence |
|---|---|---|
| ICTICT426 | `core/llm_client.py` | `RELEASES.md`, provider setup docs |
| ICTPRG302 | `dashboard/app.py`, `core/base_agent.py` | test files and commit history |
| ICTICT451 | `README.md`, `docs/quickstart.md` | security/auth sections in docs |
| ICTAII401 | `core/llm_client.py`, `agents/` | architecture notes |
| BSBXCS404 | auth + webhook controls in `dashboard/app.py` and route layers | `.env.example`, onboarding runbook |
| ICTICT443 | documentation + open-source workflow artifacts | release notes, commit log, public website updates, GitHub profile activity |
| ICTSAS432 | troubleshooting and onboarding docs | issue/change evidence |
| BSBCRT404 | fallback and architecture trade-offs in `core/job_store.py` and `core/llm_client.py` | release rationale |
| ICTCLD301 | hosted deployment docs and launch chain | onboarding + quickstart |
| ICTWEB432 | layout templates | screenshots and UI walkthrough |
| ICTWEB431 | template markup and style assets | rendered pages |
| ICTWEB434 | deployed content changes and release updates | hosted docs/workflows, live site publishing evidence, Wayback timeline continuity |
| ICTWEB433 | documented UI states and validation support | test and QA notes |
| ICTWEB450 | hosting strategy in README/quickstart | Procfile and deployment docs |
| ICTWEB452 | authored template/pages | page-level changes |
| ICTWEB443 | public-facing page optimization evidence (if available) | supplementary landing-page work |
| ICTDBS416 | `supabase-short-links.sql`, `SET_UP_GUIDE.md` (Artist-Pages) | `supabase-seed.sql`, `SUPABASE_SCHEMA.md` |
| ICTWEB451 | `supabase-seed.sql`, `supabase-short-links.sql` (Artist-Pages) | `artist-page.js` data read patterns |
| ICTICT435 | `README.md`, `docs/*`, `RELEASES.md` | this RPL evidence pack, GitHub profile/repository portfolio |
| ICTCLD401 | `supabase-config.js`, `README.md` (Artist-Pages) | `SET_UP_GUIDE.md`, deployment notes |

---

## 3. Screenshots and Attachments Checklist

Add one PDF or image set with these captures:

- [ ] Running app login page and successful login flow.
- [ ] Hub page and at least one department dashboard.
- [ ] Agents list page and one executed agent result.
- [ ] API docs page (`/apidocs/`).
- [ ] Terminal output showing test execution (for example `pytest`).
- [ ] Environment configuration example (with secrets redacted).
- [ ] Git commit history snippet showing your authored changes.
- [ ] Wayback screenshot showing earliest and latest `lrrecords.com.au` captures.
- [ ] Live site screenshot showing established branding and current operations.
- [ ] GitHub profile screenshot showing repository count and contribution activity.
- [ ] Screenshot of at least 3 representative repositories with short role notes.

---

## 4. Command Evidence (Paste Output into Submission Appendix)

Recommended command set:

```bash
git log --oneline -n 20
python -m pytest tests/test_llm_client.py -q
python dashboard/app.py
```

Optional hosted/deploy checks:

```bash
docker build -t maestro-ai .
docker run --env-file .env -p 8080:8080 maestro-ai
```

Important:
- Redact tokens, secrets, and private URLs before submission.

---

## 5. Supplementary Evidence Track - Artist-Pages (Supabase)

Purpose:
- Strengthen evidence for relational database and SQL-focused units.

External evidence location provided by candidate:
- `c:\Users\brett\Documents\lrrecords-artist-pages\artist-pages`

Concrete evidence to attach:
- `README.md`: Supabase data model summary (`public.artists`) and security model (RLS and owner-scoped writes).
- `SET_UP_GUIDE.md`: SQL DDL for table creation, RLS activation, and policy definitions.
- `supabase-seed.sql`: practical SQL `insert` and `on conflict do update` usage for application data.
- `supabase-short-links.sql`: relational SQL for `public.short_links` with primary key, `owner_id` foreign key, unique index, and RLS policies.
- `SUPABASE_SCHEMA.md`: structured schema extension documentation and operational review-state contract.
- `supabase-config.js`: cloud runtime integration and environment configuration.
- `artist-page.js`: Supabase client initialization and application-side data mapping.

Assessment-relevant SQL features demonstrated:
- `create table if not exists`.
- `references auth.users(id) on delete cascade`.
- `create unique index if not exists`.
- `insert ... on conflict (...) do update`.
- `alter table ... enable row level security`.
- `create policy` with `using` and `with check` owner constraints.

Recommended screenshot set for this supplementary pack:
- [ ] Supabase SQL editor showing `public.short_links` table and index.
- [ ] Supabase RLS policy screen for owner read/insert enforcement.
- [ ] Supabase table view showing seeded artist data rows.
- [ ] Admin portal save flow writing updated artist profile data.
- [ ] Public artist page rendering that data from Supabase.

Suggested appendix naming:
- `08_ArtistPages_Supabase_SQL_Evidence.pdf`

---

## 6. Public Presence and Long-Term Practice Evidence

Purpose:
- Provide independent, third-party evidence of sustained web operations, publishing, and software delivery over time.

Evidence sources:
- Live website: `https://lrrecords.com.au`
- Wayback timeline: `https://web.archive.org/web/*/https://lrrecords.com.au`
- GitHub profile: `https://github.com/lrrecords`
- GitHub repositories: `https://github.com/lrrecords?tab=repositories`

Observed support evidence:
- Wayback captures show archived continuity from 2002 through 2025.
- The live website demonstrates active operation with maintained services, portfolio content, and product/tool pages.
- The GitHub profile shows active repositories and recent contribution history, supporting ongoing development practice.

RPL relevance:
- Supports authenticity and recency of practical web and platform work.
- Supports website maintenance and content lifecycle evidence.
- Supports software workflow evidence through visible repository, commit, and release activity.

Suggested appendix naming:
- `09_Public_Web_and_GitHub_Continuity_Evidence.pdf`

---

## 7. Candidate Declaration Template

I confirm that the listed artifacts represent work I completed or directly contributed to, and that all submitted evidence is authentic and accurate.

Name: [Add name]  
Date: [Add date]  
Signature: [Add signature if required]
