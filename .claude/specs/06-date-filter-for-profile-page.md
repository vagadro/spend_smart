# Spec: Date Filter For Profile Page

## Overview
Add a date-range filter to the profile page so users can narrow all four data sections — summary stats, transaction history, and category breakdown — to a specific period. The filter is rendered as a row of pre-set period buttons (This Month, Last Month, Last 3 Months, This Year, All Time) that submit a GET request with a `period` query parameter. The active period is highlighted, and all three query helpers are updated to accept optional `date_from` / `date_to` bounds. This is purely a read-side enhancement; no write routes or schema changes are needed.

## Depends on
- Step 1: Database setup (expenses table with `date` column in YYYY-MM-DD format)
- Step 2: Registration
- Step 3: Login / Logout (session["user_id"] set on login)
- Step 4: Profile page static UI (template sections already exist)
- Step 5: Backend connection (real queries powering the profile page)

## Routes
- `GET /profile` — existing route, extended to accept an optional `period` query param (`this_month`, `last_month`, `last_3_months`, `this_year`, `all`). Defaults to `this_month` when the param is absent or unrecognised — logged-in only.

No new routes.

## Database changes
No database changes. The `expenses.date` column (TEXT, YYYY-MM-DD) already supports date-range filtering via SQL `BETWEEN` / `>=` / `<=`.

## Templates
- **Modify** `templates/profile.html`:
  - Add a filter bar above the summary stats section containing five period buttons that link to `?period=<value>`.
  - Apply an `active` CSS class to the button matching the current `period`.
  - Pass the resolved `period` string from the route so the template can highlight the right button.

## Files to change
- `app.py` — update `profile()` to:
  - Read `period` from `request.args` (default `"this_month"`).
  - Compute `date_from` and `date_to` (ISO strings, YYYY-MM-DD) from the period using Python's `datetime` / `date` standard-library tools.
  - Pass `date_from`, `date_to`, and `period` to all three query helpers and to the template context.
- `database/queries.py` — update `get_summary_stats`, `get_recent_transactions`, and `get_category_breakdown` to each accept `date_from=None` and `date_to=None` keyword arguments:
  - When both are provided, add `AND date BETWEEN ? AND ?` to the WHERE clause.
  - When absent, behaviour is unchanged (no date filter applied).
- `templates/profile.html` — add the filter bar (see Templates section above).
- `static/css/profile.css` — add styles for `.filter-bar`, `.filter-btn`, and `.filter-btn.active`.

## Files to create
No new files.

## New dependencies
No new dependencies. Only Python standard-library `datetime` / `date` arithmetic is needed.

## Rules for implementation
- No SQLAlchemy or ORMs — raw sqlite3 via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles; add `.filter-bar` / `.filter-btn` rules to `profile.css`
- Period-to-date computation must live in `app.py` (the view), not in `queries.py`
- Query helpers must remain pure (accept dates as strings; no Flask imports)
- An unrecognised `period` value must silently fall back to `"this_month"` — never raise an error
- `date_to` for the current period is today's date, not a fixed future date
- The user info card section is not affected by the filter

## Period definitions
| `period` value  | `date_from`                                  | `date_to`  |
|-----------------|----------------------------------------------|------------|
| `this_month`    | First day of current month (YYYY-MM-01)       | Today      |
| `last_month`    | First day of previous month                  | Last day of previous month |
| `last_3_months` | First day of the month 3 months ago           | Today      |
| `this_year`     | YYYY-01-01 (current year)                     | Today      |
| `all`           | `None` (no filter)                            | `None`     |

## Definition of done
- [ ] Visiting `/profile` without a `period` param defaults to "This Month" with the button highlighted
- [ ] Clicking each period button reloads the page with the correct `?period=` param in the URL
- [ ] Only the active period button has the `active` CSS style
- [ ] Summary stats (total spent, transaction count, top category) reflect only expenses in the selected period
- [ ] Transaction table shows only rows whose `date` falls within the selected period
- [ ] Category breakdown shows only categories with expenses in the selected period
- [ ] Selecting "All Time" shows all expenses regardless of date
- [ ] Selecting "Last Month" shows expenses for the previous calendar month only
- [ ] A new user with no expenses in the selected period sees ₹0.00, 0 transactions, and an empty breakdown — no errors
- [ ] Passing an invalid `period` value (e.g. `?period=garbage`) silently defaults to "This Month"
