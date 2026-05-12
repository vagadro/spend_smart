"""
Tests for Step 06 — Date Filter for Profile Page
Based on spec: .claude/specs/06-date-filter-for-profile-page.md
"""
import pytest
from datetime import date, timedelta

import database.db as db_module
from database.db import get_db, init_db
from database.queries import get_summary_stats, get_recent_transactions, get_category_breakdown


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _today():
    return date.today()


def _this_month_start():
    return _today().replace(day=1).isoformat()


def _last_month_start():
    first_this = _today().replace(day=1)
    return (first_this - timedelta(days=1)).replace(day=1).isoformat()


def _far_past():
    return "2020-06-15"


def _insert_expenses(user_id, rows):
    """rows: list of (amount, category, date_str, description)"""
    conn = get_db()
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [(user_id, amt, cat, dt, desc) for amt, cat, dt, desc in rows],
    )
    conn.commit()
    conn.close()


def _register_and_get_uid(client, email="filter@test.com"):
    client.post("/register", data={
        "name": "Filter User",
        "email": email,
        "password": "pass1234",
    })
    conn = get_db()
    uid = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()[0]
    conn.close()
    return uid


# ------------------------------------------------------------------ #
# Unit tests: query helpers accept date_from / date_to               #
# ------------------------------------------------------------------ #

def test_get_summary_stats_date_filter_includes_only_in_range(user_id):
    today_str = _today().isoformat()
    _insert_expenses(user_id, [
        (100.00, "Food",  today_str,   "In range"),
        (200.00, "Bills", _far_past(), "Out of range"),
    ])
    result = get_summary_stats(user_id, date_from=today_str, date_to=today_str)
    assert result["transaction_count"] == "1"
    assert result["total_spent"] == "₹100.00"


def test_get_summary_stats_date_filter_no_matches_returns_zeros(user_id):
    _insert_expenses(user_id, [(100.00, "Food", _this_month_start(), "This month")])
    result = get_summary_stats(user_id, date_from="2000-01-01", date_to="2000-01-31")
    assert result["total_spent"] == "₹0.00"
    assert result["transaction_count"] == "0"
    assert result["top_category"] == "—"


def test_get_summary_stats_no_date_filter_returns_all(user_id):
    _insert_expenses(user_id, [
        (100.00, "Food",  _this_month_start(), "This month"),
        (200.00, "Bills", _far_past(),          "Far past"),
    ])
    result = get_summary_stats(user_id)
    assert result["transaction_count"] == "2"
    assert result["total_spent"] == "₹300.00"


def test_get_recent_transactions_date_filter_returns_only_in_range(user_id):
    today_str = _today().isoformat()
    _insert_expenses(user_id, [
        (50.00, "Food",      today_str,   "Today expense"),
        (75.00, "Transport", _far_past(), "Old expense"),
    ])
    result = get_recent_transactions(user_id, date_from=today_str, date_to=today_str)
    assert len(result) == 1
    assert result[0]["description"] == "Today expense"


def test_get_recent_transactions_no_date_filter_returns_all(user_id):
    _insert_expenses(user_id, [
        (50.00, "Food",      _this_month_start(), "This month"),
        (75.00, "Transport", _far_past(),          "Old"),
    ])
    result = get_recent_transactions(user_id)
    assert len(result) == 2


def test_get_recent_transactions_empty_range_returns_empty_list(user_id):
    _insert_expenses(user_id, [(50.00, "Food", _this_month_start(), "This month")])
    result = get_recent_transactions(user_id, date_from="2000-01-01", date_to="2000-01-31")
    assert result == []


def test_get_category_breakdown_date_filter_returns_only_in_range(user_id):
    today_str = _today().isoformat()
    _insert_expenses(user_id, [
        (100.00, "Food",  today_str,   "Today"),
        (200.00, "Bills", _far_past(), "Old"),
    ])
    result = get_category_breakdown(user_id, date_from=today_str, date_to=today_str)
    assert len(result) == 1
    assert result[0]["name"] == "Food"
    assert result[0]["pct"] == 100


def test_get_category_breakdown_no_date_filter_returns_all_categories(user_id):
    _insert_expenses(user_id, [
        (100.00, "Food",  _this_month_start(), "This month"),
        (200.00, "Bills", _far_past(),          "Old"),
    ])
    result = get_category_breakdown(user_id)
    assert len(result) == 2


def test_get_category_breakdown_empty_range_returns_empty_list(user_id):
    _insert_expenses(user_id, [(100.00, "Food", _this_month_start(), "This month")])
    result = get_category_breakdown(user_id, date_from="2000-01-01", date_to="2000-01-31")
    assert result == []


# ------------------------------------------------------------------ #
# Route: auth guard                                                   #
# ------------------------------------------------------------------ #

def test_profile_unauthenticated_redirects_to_login(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ------------------------------------------------------------------ #
# Route: period param — valid values                                  #
# ------------------------------------------------------------------ #

def test_profile_no_period_param_returns_200(client):
    client.post("/register", data={"name": "U", "email": "u@t.com", "password": "pass1234"})
    assert client.get("/profile").status_code == 200


def test_profile_default_period_highlights_this_month_button(client):
    """No ?period param → 'This Month' button carries the active class."""
    client.post("/register", data={"name": "U", "email": "u@t.com", "password": "pass1234"})
    body = client.get("/profile").data.decode()
    assert "This Month" in body
    assert "active" in body


@pytest.mark.parametrize("period,label", [
    ("this_month",    "This Month"),
    ("last_month",    "Last Month"),
    ("last_3_months", "Last 3 Months"),
    ("this_year",     "This Year"),
    ("all",           "All Time"),
])
def test_profile_valid_period_returns_200_and_shows_button_label(client, period, label):
    client.post("/register", data={"name": "U", "email": "u@t.com", "password": "pass1234"})
    response = client.get(f"/profile?period={period}")
    assert response.status_code == 200
    assert label in response.data.decode()


def test_profile_invalid_period_falls_back_returns_200(client):
    client.post("/register", data={"name": "U", "email": "u@t.com", "password": "pass1234"})
    assert client.get("/profile?period=garbage").status_code == 200


def test_profile_invalid_period_defaults_to_this_month_active(client):
    """?period=garbage must silently resolve to this_month (no 500, active button visible)."""
    client.post("/register", data={"name": "U", "email": "u@t.com", "password": "pass1234"})
    body = client.get("/profile?period=garbage").data.decode()
    assert "This Month" in body
    assert "active" in body


# ------------------------------------------------------------------ #
# Route: filter bar presence                                          #
# ------------------------------------------------------------------ #

def test_profile_filter_bar_contains_all_five_buttons(client):
    client.post("/register", data={"name": "U", "email": "u@t.com", "password": "pass1234"})
    body = client.get("/profile").data.decode()
    for label in ["This Month", "Last Month", "Last 3 Months", "This Year", "All Time"]:
        assert label in body, f"Missing filter button: {label}"


def test_profile_rupee_symbol_present(client):
    client.post("/register", data={"name": "U", "email": "u@t.com", "password": "pass1234"})
    assert "₹" in client.get("/profile").data.decode()


# ------------------------------------------------------------------ #
# Route: data filtering                                               #
# ------------------------------------------------------------------ #

def test_profile_new_user_no_expenses_shows_zero_for_all_periods(client):
    """New user with no expenses → ₹0.00, 0 transactions, no errors for every period."""
    client.post("/register", data={"name": "U", "email": "u@t.com", "password": "pass1234"})
    for period in ["this_month", "last_month", "last_3_months", "this_year", "all"]:
        response = client.get(f"/profile?period={period}")
        assert response.status_code == 200, f"Got {response.status_code} for period={period}"
        assert "₹0.00" in response.data.decode(), f"Expected ₹0.00 for period={period}"


def test_profile_this_month_excludes_old_expenses(client):
    """Expenses from far past must not appear in this_month stats."""
    uid = _register_and_get_uid(client)
    _insert_expenses(uid, [
        (100.00, "Food",  _this_month_start(), "Current month"),
        (500.00, "Bills", _far_past(),          "Old expense"),
    ])
    body = client.get("/profile?period=this_month").data.decode()
    assert "₹100.00" in body
    assert "₹500.00" not in body


def test_profile_all_time_includes_all_expenses(client):
    """period=all must sum all expenses regardless of date."""
    uid = _register_and_get_uid(client)
    _insert_expenses(uid, [
        (100.00, "Food",  _this_month_start(), "Current month"),
        (200.00, "Bills", _far_past(),          "Old expense"),
    ])
    body = client.get("/profile?period=all").data.decode()
    assert "₹300.00" in body


def test_profile_last_month_excludes_this_month_expenses(client):
    """An expense dated this month must NOT appear in last_month stats."""
    uid = _register_and_get_uid(client)
    _insert_expenses(uid, [
        (100.00, "Food", _this_month_start(), "This month"),
    ])
    body = client.get("/profile?period=last_month").data.decode()
    assert "₹100.00" not in body
    assert "₹0.00" in body


def test_profile_last_month_shows_last_month_expenses(client):
    """An expense dated in the previous calendar month must appear under last_month."""
    uid = _register_and_get_uid(client)
    _insert_expenses(uid, [
        (250.00, "Transport", _last_month_start(), "Last month expense"),
    ])
    body = client.get("/profile?period=last_month").data.decode()
    assert "₹250.00" in body


def test_profile_this_year_includes_jan_first_excludes_last_year(client):
    """An expense on Jan 1 of this year is included; a 2020 expense is excluded."""
    uid = _register_and_get_uid(client)
    jan_first = date(_today().year, 1, 1).isoformat()
    _insert_expenses(uid, [
        (150.00, "Shopping", jan_first,   "Start of year"),
        (999.00, "Bills",    _far_past(), "Past year"),
    ])
    body = client.get("/profile?period=this_year").data.decode()
    assert "₹150.00" in body
    assert "₹999.00" not in body
