# Maestro AI Open Core Implementation Checklist

## 1. Define & Document Boundaries
- [x] List all modules, agents, and features in the codebase.
- [x] Mark each as “core/open” or “premium/proprietary.”
- [x] Document this boundary in `README.md` and/or a new `OPEN_CORE.md`.

## 2. Directory Structure & Refactor
- [x] Create a dedicated folder for premium/proprietary code (e.g., `premium_agents/`).
- [x] Move premium agents/features to this folder or a private repo.
- [ ] Ensure the open core runs and passes tests with premium code removed.

## 3. Agent Registry & Loader
- [x] Refactor the agent registry to dynamically discover/load agents from both open and premium locations.
- [x] Add error handling: if a premium agent is missing, log a warning but do not break the app.
- [x] Dynamic agent loader tested and working in both CLI and web contexts.

## 4. APIs & Data Flow
- [x] Confirm agent interfaces and data contracts are unchanged.
- [x] Test that both open and premium agents interact with the dashboard, job store, and data files as before.
- [x] `/agents` endpoint lists all discovered agents.
- [x] `/agents/run/<agent_name>` endpoint executes agent and returns output as JSON.
- [x] Premium agent execution tested via web endpoint.

## 5. Configuration & Extension Points
- [ ] Add config options (e.g., in `.env` or `config.py`) to enable/disable premium features.
- [x] Document how to add third-party or premium agents via extension points (see README and docs).

## 6. Documentation & Licensing
- [x] Update `README.md` to clarify what’s open, what’s premium, and how to extend.
- [ ] Update or add `CONTRIBUTING.md` and extension/plugin guides.
- [ ] Confirm the open core license (MIT or chosen).
- [ ] Add branding/trademark notes for premium features.

## 7. Testing
- [ ] Run all tests with only open core enabled.
- [ ] Run all tests with premium features enabled.
- [ ] Add/expand tests for agent loading, extension points, and error handling.

## 8. Release & Feedback
- [ ] Publish the open core repo and docs.
- [ ] Announce the Open Core model and invite feedback.
- [ ] Monitor issues and iterate on boundaries and extension points as needed.
