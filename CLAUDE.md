# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup virtual environment (uses Python 3.12 via pyenv)
pyenv local 3.12.9
python3 -m venv env3
source env3/bin/activate
pip install -r requirements.txt  # base deps (no MySQL)
# pip install -r requirements-prod.txt  # adds mysqlclient for production

# Run development server (from foodmarks/ subdirectory)
cd foodmarks && python manage.py runserver

# Run migrations
cd foodmarks && python manage.py migrate

# Run tests
cd foodmarks && python manage.py test

# Run a single test
cd foodmarks && python manage.py test fm.tests.TestClassName.test_method_name

# Create dev superuser (admin/admin) non-interactively
cd foodmarks && python manage.py create_dev_user
```

Local settings (DB credentials, etc.) go in `foodmarks/settings_local.py` — imported at the bottom of `settings.py` if present.

## Architecture

**Foodmarks** is a Django 3.2 recipe bookmarking app with social sharing. The Django project lives in the `foodmarks/` subdirectory and contains two apps: `fm` (core) and `accounts`.

### Data Model

The core concept is a three-layer model:

- **Recipe** — A global, shared entity. The `link` field is unique, so two users bookmarking the same URL share one Recipe row.
- **Ribbon** — The per-user association to a Recipe. Stores personal data: `comments`, `is_boxed`, `is_used`, `thumb` (rating: True/False/None). One ribbon per (user, recipe) pair.
- **Tag** — Per-ribbon tags (user-specific). The `key` field is deprecated; only `value` is used.
- **UserProfile** — Extends Django's User with a single `copy_tags` preference.

### Key Views (`fm/views.py`)

- `search_recipes()` — Main list view at `/search/`. Filters by query (searches title + tag values), recipe box, used/unused, thumbs-up. Shows either the current user's ribbons or all public recipes.
- `add_recipe()` / `edit_recipe()` — Both delegate to `_save_recipe()` for the shared save logic (creating/updating Recipe + Ribbon + Tags).
- `action()` — AJAX endpoint handling `changeBoxStatus` and `deleteRibbon` operations.
- `view_recipe()` — Public recipe detail page showing all users' ribbons.
- `delete_ribbon()` — Deletes the ribbon; also deletes the Recipe if no other users have a ribbon for it.

### Templates

Templates live in `foodmarks/fm/templates/` and `foodmarks/accounts/templates/accounts/`. The base template is `fm/templates/base.html`.

### Frontend

Bootstrap 4.6.2, jQuery 3.7.1, and Selectize.js (for tag autocomplete) are all loaded via CDN. Custom JS is in `foodmarks/static/js/main.js` (~60 lines). The bookmarklet at `/bookmarklet/` accepts `?url=` and `?title=` query params for quick capture from the browser.

## Agent Rules

These rules encode past failures as permanent constraints. When Claude produces an
undesired output, add a rule here rather than correcting the output manually.

### Before implementing anything
- Search the codebase first: use Grep/Glob to verify the feature doesn't already exist
- Read `progress.txt` to see what's already been done this session

### After any code change
- Run: `cd foodmarks && ruff check . --fix && ruff format . && python manage.py test`
- Do NOT mark a task complete if lint or tests fail
- Use Playwright MCP to verify UI changes in the browser at http://127.0.0.1:8000

### Task tracking (Ralph Wiggum method)
- At session start: read `spec.md` for requirements, read `progress.txt` for state
- After each completed task: update `progress.txt`, then commit
- State lives in files — not in conversation history

### Encoding failures
- When a mistake occurs, add a specific rule to this section before moving on
