# RPL Screenshot Appendix Template - ICT40120

Use this template to assemble a clean, assessor-friendly screenshot appendix.

Submission note:
- Redact secrets, private emails, API keys, and personal tokens before export.
- Use consistent naming and include one short caption under each screenshot.

---

## 1. Recommended File Naming Convention

Use this naming pattern so evidence is easy to verify:

`NN_topic_short-description.ext`

Examples:
- `01_maestro_login_success.png`
- `02_hub_dashboard_live.png`
- `03_agents_result_example.png`
- `04_api_docs_apidocs.png`
- `05_pytest_pass_output.png`
- `06_env_redacted_example.png`
- `07_git_log_authored_changes.png`
- `08_wayback_earliest_latest.png`
- `09_lrrecords_live_site_ops.png`
- `10_github_profile_contributions.png`
- `11_github_repos_representative.png`

---

## 2. Screenshot Capture Checklist with Captions

| No. | Evidence Item | What to Capture | Suggested Filename | Caption Template |
|---|---|---|---|---|
| 1 | Running app login flow | Login page + successful authenticated transition | `01_maestro_login_success.png` | `Maestro authentication flow showing successful login to the application.` |
| 2 | Hub/department dashboard | Hub page and one department view | `02_hub_dashboard_live.png` | `Main dashboard and department interface demonstrating implemented web UI workflows.` |
| 3 | Agent execution result | Agents list + one completed task/result | `03_agents_result_example.png` | `Agent execution output demonstrating practical orchestration and result delivery.` |
| 4 | API docs | `/apidocs/` rendered page | `04_api_docs_apidocs.png` | `Auto-generated API documentation endpoint available in the deployed/local web app.` |
| 5 | Test execution | Terminal output from `python -m pytest tests/test_llm_client.py -q` | `05_pytest_pass_output.png` | `Automated test execution evidence showing validation of key application behavior.` |
| 6 | Environment configuration | Redacted `.env` example or settings screen | `06_env_redacted_example.png` | `Environment configuration evidence with sensitive credentials redacted.` |
| 7 | Git history | `git log --oneline -n 20` showing authored commits | `07_git_log_authored_changes.png` | `Version control history demonstrating iterative development and authored changes.` |
| 8 | Wayback continuity | Wayback page showing earliest and latest captures for `lrrecords.com.au` | `08_wayback_earliest_latest.png` | `Independent archival evidence showing long-term public website continuity over time.` |
| 9 | Live site operations | Current `lrrecords.com.au` page showing active services/content | `09_lrrecords_live_site_ops.png` | `Current production website with maintained content and active service offerings.` |
| 10 | GitHub profile activity | `github.com/lrrecords` overview (repos + contribution activity) | `10_github_profile_contributions.png` | `Public software development profile showing repositories and ongoing contribution activity.` |
| 11 | Representative repositories | At least 3 repos with short role notes | `11_github_repos_representative.png` | `Representative repository portfolio showing breadth of applied web/software work.` |

---

## 3. Representative Repository Notes (Paste Under Screenshot 11)

Use this mini-template under the repository screenshot:

1. Repository: [name]
- Purpose: [one-line summary]
- My contribution: [one-line summary]
- Skills evidenced: [web/backend/frontend/devops/docs/testing]

2. Repository: [name]
- Purpose: [one-line summary]
- My contribution: [one-line summary]
- Skills evidenced: [web/backend/frontend/devops/docs/testing]

3. Repository: [name]
- Purpose: [one-line summary]
- My contribution: [one-line summary]
- Skills evidenced: [web/backend/frontend/devops/docs/testing]

---

## 4. Export and Packaging Guide

1. Capture all screenshots in PNG format where possible.
2. Keep filenames in numeric order.
3. Add one caption below each image using the template text.
4. Export as one PDF appendix:
- `09_Public_Web_and_GitHub_Continuity_Evidence.pdf` (public corroboration set)
- Or include all items in a single combined appendix if your assessor prefers one file.
5. Validate that all sensitive values are redacted before submission.
