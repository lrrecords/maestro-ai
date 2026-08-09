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
| ICTICT443 | documentation + open-source workflow artifacts | release notes and commit log |
| ICTSAS432 | troubleshooting and onboarding docs | issue/change evidence |
| BSBCRT404 | fallback and architecture trade-offs in `core/job_store.py` and `core/llm_client.py` | release rationale |
| ICTCLD301 | hosted deployment docs and launch chain | onboarding + quickstart |
| ICTWEB432 | layout templates | screenshots and UI walkthrough |
| ICTWEB431 | template markup and style assets | rendered pages |
| ICTWEB434 | deployed content changes and release updates | hosted docs/workflows |
| ICTWEB433 | documented UI states and validation support | test and QA notes |
| ICTWEB450 | hosting strategy in README/quickstart | Procfile and deployment docs |
| ICTWEB452 | authored template/pages | page-level changes |
| ICTWEB443 | public-facing page optimization evidence (if available) | supplementary landing-page work |
| ICTDBS416 | supplementary relational DB project evidence | Artist-Pages/Supabase pack |
| ICTWEB451 | supplementary SQL query evidence | Artist-Pages/Supabase pack |
| ICTICT435 | `README.md`, `docs/*`, `RELEASES.md` | this RPL evidence pack |
| ICTCLD401 | environment and deployment configuration docs | hosted runbooks |

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

Current workspace status:
- `artist-pages/admin/` exists but is empty in this snapshot.

When available, include:
- Supabase migration/schema files.
- SQL query examples used by features.
- Table relationship diagrams.
- CRUD forms and data-flow screenshots.
- Auth and row-level security configuration evidence.

Suggested appendix naming:
- `08_ArtistPages_Supabase_SQL_Evidence.pdf`

---

## 6. Candidate Declaration Template

I confirm that the listed artifacts represent work I completed or directly contributed to, and that all submitted evidence is authentic and accurate.

Name: [Add name]  
Date: [Add date]  
Signature: [Add signature if required]
