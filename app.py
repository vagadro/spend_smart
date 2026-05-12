import os
from datetime import date, timedelta

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-change-in-prod")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Context processors                                                  #
# ------------------------------------------------------------------ #

@app.context_processor
def inject_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return {"current_user": None}
    conn = get_db()
    try:
        user = conn.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    return {"current_user": user}


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name:
        return render_template("register.html", error="Name is required.", name=name, email=email)
    if not email:
        return render_template("register.html", error="Email is required.", name=name, email=email)
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.", name=name, email=email)

    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()

    if existing:
        return render_template("register.html", error="An account with that email already exists.", name=name, email=email)

    password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()

    session["user_id"] = new_id
    flash("Welcome to Spendly! Your account has been created.", "success")
    return redirect(url_for("landing"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.", email=email)

    session.clear()
    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


def _period_dates(period):
    today = date.today()
    if period == "last_month":
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        return last_prev.replace(day=1).isoformat(), last_prev.isoformat()
    if period == "last_3_months":
        first_this = today.replace(day=1)
        m1 = (first_this - timedelta(days=1)).replace(day=1)
        m2 = (m1 - timedelta(days=1)).replace(day=1)
        m3 = (m2 - timedelta(days=1)).replace(day=1)
        return m3.isoformat(), today.isoformat()
    if period == "this_year":
        return date(today.year, 1, 1).isoformat(), today.isoformat()
    if period == "all":
        return None, None
    # default: this_month
    return today.replace(day=1).isoformat(), today.isoformat()


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    uid = session["user_id"]

    # Custom date range takes priority over pre-set period buttons
    custom_from = request.args.get("date_from", "").strip()
    custom_to = request.args.get("date_to", "").strip()
    period = None

    if custom_from and custom_to:
        try:
            date.fromisoformat(custom_from)
            date.fromisoformat(custom_to)
            date_from, date_to = custom_from, custom_to
        except ValueError:
            custom_from = custom_to = ""

    if not (custom_from and custom_to):
        valid_periods = {"this_month", "last_month", "last_3_months", "this_year", "all"}
        period = request.args.get("period", "this_month")
        if period not in valid_periods:
            period = "this_month"
        date_from, date_to = _period_dates(period)
        custom_from = custom_to = ""

    user = get_user_by_id(uid)
    summary = get_summary_stats(uid, date_from=date_from, date_to=date_to)
    stats = [
        {"label": "Total Spent",  "value": summary["total_spent"]},
        {"label": "Transactions", "value": summary["transaction_count"]},
        {"label": "Top Category", "value": summary["top_category"]},
    ]
    transactions = get_recent_transactions(uid, date_from=date_from, date_to=date_to)
    categories = get_category_breakdown(uid, date_from=date_from, date_to=date_to)
    return render_template("profile.html",
                           user=user, stats=stats,
                           transactions=transactions,
                           categories=categories,
                           period=period,
                           custom_from=custom_from,
                           custom_to=custom_to)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
