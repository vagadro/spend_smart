# Spec: Registration

## Overview
Implement the user registration flow so new visitors can create a Spendly account. The `/register` route currently only renders the form via GET; this step wires up the POST handler to validate input, hash the password, insert the user into the `users` table. On success the user is shown with a success message and then redirect to the dashboard (or back to the form with an inline error). This is the first authenticated action in the app and is a prerequisite for every subsequent logged-in feature.

## Depends on
- Step 1 — Database setup (`users` table must exist via `init_db()`)

## Routes
- `GET  /register` — render the registration form — public
- `POST /register` — validate input, create user, start session, redirect — public

## Database changes
No database changes. The `users` table already exists with the required columns (`id`, `name`, `email`, `password_hash`, `created_at`).

## Templates
- **Modify** `templates/register.html` — already contains the form; add `{{ error }}` display block (already present) and ensure `value` attributes repopulate `name` and `email` fields after a failed submission so the user does not have to retype them.

## Files to change
- `app.py` — add POST handler for `/register`; import `session`, `redirect`, `url_for`, `request` from Flask; import `generate_password_hash` from `werkzeug.security`; set `app.secret_key`
- `templates/register.html` — add `value="{{ name or '' }}"` and `value="{{ email or '' }}"` to the name and email inputs so fields are sticky on error

## Files to create
No new files.

## New dependencies
No new dependencies. `werkzeug` is already installed with Flask.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite via `get_db()`
- Parameterised queries only — never interpolate user input into SQL strings
- Passwords hashed with `werkzeug.security.generate_password_hash` (method `pbkdf2:sha256`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use Flask's built-in `session` (dict-based) — do not introduce a third-party auth library
- Set `app.secret_key` from an env var (`SECRET_KEY`) with a hard-coded fallback only for development
- Validation order: name not empty → email not empty → password ≥ 8 chars → email not already taken
- On duplicate email, show a clear inline error; do **not** reveal whether the email exists to an outside observer (acceptable for a student project but note the trade-off)
- After successful registration, start the session (`session['user_id'] = user.id`) and redirect to `/` (or `/dashboard` if that route exists by this step — default to `/`)
- Flash messages are optional; inline `error` template variable is sufficient and already wired in `register.html`

## Definition of done
- [ ] Visiting `/register` renders the form (GET still works)
- [ ] Submitting with an empty name shows an inline error and keeps the email field populated
- [ ] Submitting with a password shorter than 8 characters shows an inline error
- [ ] Submitting with an already-registered email shows an inline error
- [ ] Submitting valid details inserts a row into `users` (verify with `sqlite3 spendly.db "SELECT * FROM users;"`)
- [ ] The stored `password_hash` is NOT the plain-text password
- [ ] After successful registration the user is redirected (HTTP 302) and not left on `/register`
- [ ] `session['user_id']` is set after registration (verifiable via Flask debug toolbar or a temporary `{{ session }}` dump in a template)
- [ ] Registering a second account with a different email succeeds independently
