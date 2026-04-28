# Maestro AI — Open Core Release Guide

This guide covers the steps to publish, announce, and maintain the Open Core version of Maestro AI.

---

## 1. Pre-Release Checklist

- [x] Confirm all premium/proprietary code is separated (see `premium_agents/`).
- [x] Ensure `.env` has `PREMIUM_FEATURES_ENABLED` flag and test with both true/false.
- [x] Run all tests with premium enabled and disabled.
- [x] Update all documentation (README, CHECKLIST, BOUNDARIES, EXTENDING, etc.).
- [x] Confirm license and branding notes are present.

## 2. Publishing

- Tag a release in GitHub (e.g., `v1.4.0-opencore`).
- Push all docs and code to the public repo.
- Optionally, publish a Docker image to Docker Hub.

## 3. Announcing

- Announce on GitHub Discussions, social media, and relevant communities.
- Invite feedback and contributions.
- Link to the Open Core checklist and extension guide.

## 4. Ongoing Maintenance

- Monitor issues and PRs.
- Iterate on boundaries and extension points as needed.
- Keep documentation and extension/plugin guides up to date.

---

For questions, open an issue or contact the maintainers.
