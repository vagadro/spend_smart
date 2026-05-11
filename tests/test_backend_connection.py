from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)
from database.db import get_db


# ------------------------------------------------------------------ #
# get_user_by_id                                                      #
# ------------------------------------------------------------------ #

def test_get_user_by_id_valid(user_id):
    result = get_user_by_id(user_id)
    assert result is not None
    assert result["name"] == "Test User"
    assert result["email"] == "test@test.com"
    assert result["initials"] == "TU"
    assert result["member_since"] != "—"


def test_get_user_by_id_nonexistent(db):
    result = get_user_by_id(99999)
    assert result is None


# ------------------------------------------------------------------ #
# get_summary_stats                                                   #
# ------------------------------------------------------------------ #

def test_get_summary_stats_with_expenses(seeded_user_id):
    result = get_summary_stats(seeded_user_id)
    assert result["total_spent"] == "₹190.50"
    assert result["transaction_count"] == "3"
    assert result["top_category"] == "Bills"


def test_get_summary_stats_no_expenses(user_id):
    result = get_summary_stats(user_id)
    assert result["total_spent"] == "₹0.00"
    assert result["transaction_count"] == "0"
    assert result["top_category"] == "—"


# ------------------------------------------------------------------ #
# get_recent_transactions                                             #
# ------------------------------------------------------------------ #

def test_get_recent_transactions_with_expenses(seeded_user_id):
    result = get_recent_transactions(seeded_user_id)
    assert len(result) == 3
    # newest-first: Apr 08 > Apr 05 > Apr 01
    assert result[0]["date"] == "Apr 08"
    assert result[0]["category"] == "Transport"
    assert result[0]["amount"] == "₹25.00"
    for item in result:
        assert set(item.keys()) == {"date", "description", "category", "amount"}


def test_get_recent_transactions_no_expenses(user_id):
    result = get_recent_transactions(user_id)
    assert result == []


def test_get_recent_transactions_respects_limit(seeded_user_id):
    result = get_recent_transactions(seeded_user_id, limit=2)
    assert len(result) == 2


# ------------------------------------------------------------------ #
# get_category_breakdown                                              #
# ------------------------------------------------------------------ #

def test_get_category_breakdown_with_expenses(seeded_user_id):
    result = get_category_breakdown(seeded_user_id)
    assert len(result) == 3
    # ordered by amount desc: Bills (120) > Food (45.50) > Transport (25)
    assert result[0]["name"] == "Bills"
    assert result[0]["amount"] == "₹120.00"
    total_pct = sum(item["pct"] for item in result)
    assert total_pct == 100
    for item in result:
        assert set(item.keys()) == {"name", "amount", "pct"}


def test_get_category_breakdown_no_expenses(user_id):
    result = get_category_breakdown(user_id)
    assert result == []


def test_get_category_breakdown_pct_sums_to_100(seeded_user_id):
    result = get_category_breakdown(seeded_user_id)
    assert sum(item["pct"] for item in result) == 100


# ------------------------------------------------------------------ #
# Route tests                                                         #
# ------------------------------------------------------------------ #

def test_profile_unauthenticated_redirects(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_authenticated_returns_200(client):
    # Register then check profile
    client.post("/register", data={
        "name": "Route User",
        "email": "route@test.com",
        "password": "password123",
    })
    response = client.get("/profile")
    assert response.status_code == 200
    body = response.data.decode()
    assert "Route User" in body
    assert "route@test.com" in body
    assert "₹" in body
