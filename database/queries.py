from database.db import get_db
from datetime import datetime


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


def get_summary_stats(user_id):
    conn = get_db()
    try:
        total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
        count = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
        top_row = conn.execute(
            "SELECT category FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return {
            "total_spent": f"₹{total:,.2f}",
            "transaction_count": str(count),
            "top_category": top_row["category"] if top_row else "—",
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT ?",
            (user_id, limit),
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


def get_category_breakdown(user_id):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC",
            (user_id,),
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
        # Adjust the largest-amount category's pct so all pcts sum to exactly 100
        remainder = 100 - sum(item["pct"] for item in result)
        result[0]["pct"] += remainder
        return result
    finally:
        conn.close()
