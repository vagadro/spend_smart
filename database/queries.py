from database.db import get_db
from datetime import datetime


def _date_clause(date_from, date_to):
    if date_from and date_to:
        return " AND date BETWEEN ? AND ?", (date_from, date_to)
    return "", ()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    parts = row["name"].strip().split()
    initials = "".join(p[0].upper() for p in parts[:2])
    try:
        member_since = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")
    except (ValueError, TypeError):
        member_since = "—"
    return {
        "name": row["name"],
        "email": row["email"],
        "initials": initials,
        "member_since": member_since,
    }


def get_summary_stats(user_id, date_from=None, date_to=None):
    conn = get_db()
    try:
        date_filter, date_params = _date_clause(date_from, date_to)
        total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?" + date_filter,
            (user_id, *date_params),
        ).fetchone()[0]
        count = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?" + date_filter,
            (user_id, *date_params),
        ).fetchone()[0]
        top_row = conn.execute(
            "SELECT category FROM expenses WHERE user_id = ?" + date_filter + " GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            (user_id, *date_params),
        ).fetchone()
        return {
            "total_spent": f"₹{total:,.2f}",
            "transaction_count": str(count),
            "top_category": top_row["category"] if top_row else "—",
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    conn = get_db()
    try:
        date_filter, date_params = _date_clause(date_from, date_to)
        rows = conn.execute(
            "SELECT date, description, category, amount FROM expenses WHERE user_id = ?" + date_filter + " ORDER BY date DESC LIMIT ?",
            (user_id, *date_params, limit),
        ).fetchall()
        result = []
        for row in rows:
            result.append({
                "date": datetime.strptime(row["date"], "%Y-%m-%d").strftime("%b %d"),
                "description": row["description"],
                "category": row["category"],
                "amount": f"₹{row['amount']:,.2f}",
            })
        return result
    finally:
        conn.close()


def get_category_breakdown(user_id, date_from=None, date_to=None):
    conn = get_db()
    try:
        date_filter, date_params = _date_clause(date_from, date_to)
        rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ?" + date_filter + " GROUP BY category ORDER BY total DESC",
            (user_id, *date_params),
        ).fetchall()
        if not rows:
            return []
        grand_total = sum(row["total"] for row in rows)
        result = []
        for row in rows:
            pct = round(row["total"] / grand_total * 100)
            result.append({
                "name": row["category"],
                "amount": f"₹{row['total']:,.2f}",
                "pct": pct,
            })
        # Adjust the largest-amount category so all pcts sum to exactly 100
        remainder = 100 - sum(item["pct"] for item in result)
        result[0]["pct"] += remainder
        return result
    finally:
        conn.close()
