# Spec: Login and Logout

## Overview
Implement the login POST handler and the logout route so registered users can authenticate and end their sessions. The `GET /login` route already renders the form; this step wires up the POST handler to verify credentials against the stored password hash, set the session, and redirect on success. The `/logout` route currently returns a plain string stub — this step clears the session and redirects to the landing page. `base.html`'s navbar also needs to show context-aware links (Sign in / Get started when logged out; a logout link when logged in) so the UI reflects authentication state across every page.

## Depends on
- Step 1 — Database setup (`users` table must exist with `email` and `password_hash` columns)
- Step 2 — Registration (at least one user must exist to log in with; session/secret key pattern is already established)

## Routes
- `GET  /login`  — render login form — public (already exists, no change)
- `POST /login`  — validate credentials, set session, redirect — public
- `GET  /logout` — clear session, redirect to `/` — logged-in (stub already exists, replace string return)

## Database changes
No database changes. The `users` table already has all required columns.

## Templates
- **Modify** `templates/login.html` — add `value="{{ email or '' }}"` to the email input so the field is sticky after a failed login attempt.
- **Modify** `templates/base.html` — update the `nav-links` block to show `Sign in` / `Get started` when `session.user_id` is absent, and `Sign out` when it is present.

## Files to change
- `app.py` — add POST handler to `/login` route (change `methods` to `["GET", "POST"]`); import `check_password_hash` from `werkzeug.security`; replace `/logout` stub with a real implementation that calls `session.clear()` and redirects.
- `templates/login.html` — sticky email field on error.
- `templates/base.html` — conditional nav links based on `session.get('user_id')`.

## Files to create
No new files.

## New dependencies
No new dependencies. `werkzeug` is already installed with Flask.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite via `get_db()`
- Parameterised queries only — never interpolate user input into SQL strings
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plain text
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use Flask's built-in `session` — do not introduce a third-party auth library
- On failed login show a single generic error ("Invalid email or password.") — do not reveal which field was wrong
- After successful login set `session['user_id']` and redirect to `url_for('landing')` (dashboard route does not exist yet)
- `session.clear()` is preferred over `session.pop('user_id')` for logout so any future session keys are also removed
- The `/logout` route must redirect, not render a template — a GET redirect to `/` is sufficient at this stage

## Definition of done
- [ ] `GET /login` still renders the form (no regression)
- [ ] Submitting the form with an email that does not exist shows "Invalid email or password." inline
- [ ] Submitting with a correct email but wrong password shows "Invalid email or password." inline
- [ ] After a failed login the email field is pre-filled with the submitted value
- [ ] Submitting valid credentials sets `session['user_id']` and redirects to `/` (HTTP 302)
- [ ] After login, the navbar shows a "Sign out" link instead of "Sign in" / "Get started"
- [ ] Visiting `/logout` clears the session and redirects to `/` (HTTP 302)
- [ ] After logout, the navbar reverts to "Sign in" / "Get started"
- [ ] Visiting `/logout` when already logged out does not raise an error (session.clear() is safe on empty session)
