# Spec: Harness Verification & Completion

## Goal

Verify and complete the local development harness so that Claude can be handed tasks
with confidence that: the app boots, tests run, CI is green, Playwright MCP works for
UI verification, and a dev fixture exists for manual browsing.

## Current State (verified 2026-03-10)

- ✅ venv (env3, Python 3.12) installed
- ✅ `settings_local.py` created — SQLite, no MySQL needed locally
- ✅ `python manage.py migrate` — all migrations applied
- ✅ `python manage.py test` — 2 placeholder tests pass
- ✅ Dev server starts (`runserver`)
- ✅ ruff + pre-commit installed and passing
- ✅ `~/.claude/mcp.json` exists with Playwright config
- ✅ Playwright Chromium downloaded
- ✅ `.github/workflows/ci.yml` exists (not yet pushed/verified)
- ⚠️  Existing tests are stubs (`1 + 1 == 2`) — no real coverage

## Tasks

- [ ] **Task 1: Create dev superuser** — acceptance criteria: `manage.py createsuperuser`
  documented in CLAUDE.md; a `create_dev_user` management command or fixture entry
  exists so Claude can bootstrap a user non-interactively.

- [ ] **Task 2: Create sample data fixture** — acceptance criteria: a file
  `foodmarks/fm/fixtures/sample_data.json` with ~10 recipe bookmarks (varied tags,
  some boxed, some used, mix of thumbs) assigned to the dev user; `manage.py loaddata
  sample_data` loads without errors and `/search/` shows results after login.

- [ ] **Task 3: Write real Django unit tests** — acceptance criteria: tests cover the
  core views (`search_recipes`, `add_recipe`, `edit_recipe`, `delete_ribbon`, `action`)
  and the Recipe/Ribbon model methods; all pass with `manage.py test`; no placeholder
  tests remain.

- [ ] **Task 4: Verify Playwright MCP works** — acceptance criteria: Claude starts the
  dev server as a background process (`python manage.py runserver &`), navigates to
  `http://127.0.0.1:8000` via Playwright MCP, takes a screenshot confirming a visible
  page (login screen or recipe list), then stops the server. Documented in CLAUDE.md.

- [ ] **Task 5: Push to GitHub and verify CI** — acceptance criteria: create a branch
  `harness-verification`, push it, open a pull request against master, and confirm the
  Actions workflow goes green (lint + format + tests pass).

## Out of Scope

- No Playwright automated test suite (manual verification only via MCP)
- No factory_boy or other test data libraries — plain Django fixtures and inline test setup
- No production DB access or data import

## Decision Log

- 2026-03-10: Testing strategy = Django unit tests only (no Playwright test suite)
- 2026-03-10: Mock data = superuser + fixture with ~10 realistic recipe bookmarks
- 2026-03-10: CI = push to GitHub and verify green
- 2026-03-10: Mock data will be hand-crafted (not imported from prod)

## Completion Signal

All tasks checked. `python manage.py test` passes. CI green. `progress.txt` reads "COMPLETE".
