import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module
from database.db import init_db, get_db


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test.db"))
    init_db()
    yield


@pytest.fixture
def user_id(db):
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "test@test.com", generate_password_hash("password123", method="pbkdf2:sha256")),
    )
    conn.commit()
    uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return uid


@pytest.fixture
def seeded_user_id(user_id):
    """user_id with 3 sample expenses inserted."""
    conn = get_db()
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 120.00, "Bills",    "2026-04-01", "Internet bill"),
            (user_id, 45.50,  "Food",     "2026-04-05", "Groceries"),
            (user_id, 25.00,  "Transport","2026-04-08", "Uber"),
        ],
    )
    conn.commit()
    conn.close()
    return user_id


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test.db"))
    import app as app_module
    # Re-init so the test DB is set up (app startup already called init_db on prod DB)
    init_db()
    app_module.app.config["TESTING"] = True
    app_module.app.config["SECRET_KEY"] = "test-secret"
    with app_module.app.test_client() as c:
        yield c
