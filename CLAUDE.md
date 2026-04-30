# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development server

Always use the virtualenv and run with debug mode so the server auto-reloads on code changes:

```bash
source venv/bin/activate
flask run --port 5002 --debug
```

`app.py` also has `app.run(debug=True, port=5001)` for direct execution, but `flask run` is preferred.

## Testing

```bash
source venv/bin/activate
pytest                        # run all tests
pytest tests/test_foo.py      # run a single file
pytest -k "test_name"         # run a single test by name
```

Test dependencies (`pytest`, `pytest-flask`) are already in `requirements.txt`.

## Architecture

This is a Flask + SQLite expense-tracking app built as a step-by-step student project. Most backend features are stubs — only the public-facing pages are implemented so far.

**`app.py`** is the entire backend. All routes live here; there are no blueprints.

**`database/db.py`** is a placeholder. Students will implement three functions:
- `get_db()` — SQLite connection with `row_factory` and foreign keys
- `init_db()` — `CREATE TABLE IF NOT EXISTS` for all tables
- `seed_db()` — sample data for development

**Templates** all extend `templates/base.html`, which provides the navbar, footer (with T&C and Privacy links), and loads `static/css/style.css` + `static/js/main.js`. Page-specific CSS is added via `{% block head %}` (e.g. `landing.css` for the landing page only). Page-specific JS goes in `{% block scripts %}`.

**CSS split:**
- `static/css/style.css` — global design tokens (CSS variables), reset, navbar, footer, auth pages, buttons, shared components
- `static/css/landing.css` — landing page hero overrides and landing-only components (loaded only on `/`)

**Placeholder routes** (return plain strings, not templates): `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`. These are the steps students will implement next.

## Conventions

- No JS framework — vanilla JS only. Page-specific scripts go in `{% block scripts %}` at the bottom of the relevant template.
- All design tokens are CSS variables in `style.css` under `:root`. Use them (`--ink`, `--accent`, `--paper`, etc.) rather than hard-coded colours.
- New static pages (terms, privacy, etc.) reuse the `.terms-page` CSS classes from `style.css`.
