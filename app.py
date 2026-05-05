import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db

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


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    conn = get_db()
    try:
        db_user = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
    finally:
        conn.close()

    parts = db_user["name"].strip().split()
    initials = "".join(p[0].upper() for p in parts[:2])
    try:
        from datetime import datetime
        member_since = datetime.strptime(db_user["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")
    except (ValueError, TypeError):
        member_since = "—"

    user = {
        "name": db_user["name"],
        "email": db_user["email"],
        "initials": initials,
        "member_since": member_since,
    }
    stats = [
        {"label": "Total Spent",  "value": "₹4,872.50"},
        {"label": "Transactions", "value": "24"},
        {"label": "Top Category", "value": "Food"},
    ]
    transactions = [
        {"date": "Apr 25", "description": "Restaurant dinner",    "category": "Food",          "amount": "₹22.75"},
        {"date": "Apr 22", "description": "Miscellaneous",        "category": "Other",         "amount": "₹30.00"},
        {"date": "Apr 20", "description": "Clothes",              "category": "Shopping",      "amount": "₹89.99"},
        {"date": "Apr 15", "description": "Netflix subscription", "category": "Entertainment", "amount": "₹15.00"},
        {"date": "Apr 12", "description": "Pharmacy",             "category": "Health",        "amount": "₹60.00"},
    ]
    categories = [
        {"name": "Food",      "amount": "₹68.25",  "pct": 44},
        {"name": "Bills",     "amount": "₹120.00", "pct": 25},
        {"name": "Shopping",  "amount": "₹89.99",  "pct": 20},
        {"name": "Transport", "amount": "₹25.00",  "pct": 11},
    ]
    return render_template("profile.html",
                           user=user, stats=stats,
                           transactions=transactions,
                           categories=categories)


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
