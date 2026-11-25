import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from flask import current_app, g

PASSWORD_HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, hash_len=32, salt_len=16)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_db():
    if "db" not in g:
        d1 = current_app.config.get("D1_DATABASE")
        if d1 is not None:
            g.db = D1Connection(d1)
            return g.db
        database = current_app.config["DATABASE"]
        Path(database).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        g.db = connection
    return g.db


def initialize_d1(binding):
    schema_path = Path(__file__).with_name("schema.sql")
    schema = schema_path.read_text(encoding="utf-8")
    connection = D1Connection(binding)
    connection.executescript(schema)
    _seed_d1(connection)
    connection.commit()


def _seed_d1(db):
    users = [
        ("student", "student@example.test", "Student@12345", "Student Player", "user"),
        ("admin", "admin@example.test", "Admin@12345", "Lab Administrator", "admin"),
    ]
    for username, email, password, display_name, role in users:
        if not db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            db.execute("INSERT INTO users(username,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?)", (username,email,PASSWORD_HASHER.hash(password),display_name,role,utc_now()))
    categories = ["Arcade", "Puzzle", "Strategy", "Action"]
    for name in categories:
        db.execute("INSERT OR IGNORE INTO categories(name,slug) VALUES(?,?)", (name,name.lower()))
    games = [
        ("orbital-drift", "Orbital Drift", "Arcade", "Pilot a tiny research craft through a calm field of drifting asteroids. A short original browser game made for this training lab.", "Easy", "app/static/downloads/orbital-drift.zip", "★ 4.8", "#46d6c5"),
        ("signal-garden", "Signal Garden", "Puzzle", "Route a signal through a small grid of mirrors and relays.", "Relaxed", "app/static/downloads/signal-garden.zip", "★ 4.6", "#b6a0ff"),
        ("tiny-kingdoms", "Tiny Kingdoms", "Strategy", "Arrange friendly outposts and keep their supply lines connected.", "Thoughtful", "app/static/downloads/tiny-kingdoms.zip", "★ 4.7", "#f0bd6b"),
        ("pixel-sprint", "Pixel Sprint", "Action", "A compact keyboard-first obstacle course with original shapes.", "Fast", "app/static/downloads/pixel-sprint.zip", "★ 4.5", "#ff8a80"),
    ]
    for slug,title,category,description,difficulty,file_path,rating,accent in games:
        row = db.execute("SELECT id FROM categories WHERE name = ?", (category,)).fetchone()
        db.execute("INSERT OR IGNORE INTO games(slug,title,category_id,description,difficulty,file_path,rating,accent,artwork_slug,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (slug,title,row["id"],description,difficulty,file_path,rating,accent,slug,utc_now()))


class D1Result:
    def __init__(self, result):
        payload = result.results if hasattr(result, "results") else result
        self.rows = payload.get("results", []) if isinstance(payload, dict) else []
        self.index = 0
        self.rowcount = payload.get("meta", {}).get("changes", 0) if isinstance(payload, dict) else 0
        self.lastrowid = payload.get("meta", {}).get("last_row_id") if isinstance(payload, dict) else None

    def fetchone(self):
        if self.index >= len(self.rows):
            return None
        row = self.rows[self.index]
        self.index += 1
        return D1Row(row)

    def fetchall(self):
        rows = self.rows[self.index:]
        self.index = len(self.rows)
        return [D1Row(row) for row in rows]


class D1Row(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            key = list(self.keys())[key]
        return super().__getitem__(key)


class D1Connection:
    """Small sqlite-compatible adapter for Cloudflare's Python D1 binding."""
    def __init__(self, binding):
        self.binding = binding

    def execute(self, sql, params=()):
        statement = self.binding.prepare(sql).bind(*params)
        return D1Result(statement.run())

    def executescript(self, sql):
        for statement in sql.split(";"):
            if statement.strip():
                self.execute(statement)

    def commit(self):
        return None

    def close(self):
        return None


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def initialize_database(app):
    if app.config.get("D1_DATABASE") is not None:
        return
    schema = Path(app.root_path, "schema.sql").read_text(encoding="utf-8")
    with app.app_context():
        db = get_db()
        db.executescript(schema)
        seed_database(db)
        db.commit()
        app.teardown_appcontext(close_db)


def seed_database(db):
    users = [
        ("student", "student@example.test", "Student@12345", "Student Player", "user"),
        ("admin", "admin@example.test", "Admin@12345", "Lab Administrator", "admin"),
    ]
    for username, email, password, display_name, role in users:
        exists = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if not exists:
            db.execute(
                "INSERT INTO users(username,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?)",
                (username, email, PASSWORD_HASHER.hash(password), display_name, role, utc_now()),
            )
    categories = ["Arcade", "Puzzle", "Strategy", "Action"]
    for category in categories:
        db.execute("INSERT OR IGNORE INTO categories(name,slug) VALUES(?,?)", (category, category.lower()))
    games = [
        ("orbital-drift", "Orbital Drift", "Arcade", "Pilot a tiny research craft through a calm field of drifting asteroids. A short original browser game made for this local training lab.", "Easy", "app/static/downloads/orbital-drift.zip", "★ 4.8", "#46d6c5"),
        ("signal-garden", "Signal Garden", "Puzzle", "Route a signal through a small grid of mirrors and relays. No account data or network access is used by the demo.", "Relaxed", "app/static/downloads/signal-garden.zip", "★ 4.6", "#b6a0ff"),
        ("tiny-kingdoms", "Tiny Kingdoms", "Strategy", "Arrange a handful of friendly outposts and keep their supply lines connected in this fictional turn-based challenge.", "Thoughtful", "app/static/downloads/tiny-kingdoms.zip", "★ 4.7", "#f0bd6b"),
        ("pixel-sprint", "Pixel Sprint", "Action", "A compact, keyboard-first obstacle course with original shapes and sounds. Built as a harmless sample download.", "Fast", "app/static/downloads/pixel-sprint.zip", "★ 4.5", "#ff8a80"),
    ]
    for slug, title, category_name, description, difficulty, file_path, rating, accent in games:
        category = db.execute("SELECT id FROM categories WHERE name = ?", (category_name,)).fetchone()
        db.execute(
            "INSERT OR IGNORE INTO games(slug,title,category_id,description,difficulty,file_path,rating,accent,artwork_slug,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (slug, title, category["id"], description, difficulty, file_path, rating, accent, slug, utc_now()),
        )


def verify_password(encoded, password):
    try:
        return PASSWORD_HASHER.verify(encoded, password)
    except (VerifyMismatchError, VerificationError, TypeError):
        return False


def hash_password(password):
    return PASSWORD_HASHER.hash(password)


def log_security_event(event_type, username=None, details="", user_id=None):
    db = get_db()
    from flask import request
    db.execute(
        "INSERT INTO security_logs(user_id,event_type,username,ip_address,details,created_at) VALUES(?,?,?,?,?,?)",
        (user_id, event_type, (username or "")[:80], (request.remote_addr or "local")[:60], details[:240], utc_now()),
    )


def update_login_failure(user_row):
    db = get_db()
    count = int(user_row["failed_login_count"] or 0) + 1
    delay_seconds = min(2 ** min(count - 1, 2), 4)
    locked_until = None
    if count >= 5:
        from datetime import timedelta
        locked_until = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(timespec="seconds")
        count = 0
    db.execute("UPDATE users SET failed_login_count=?,locked_until=? WHERE id=?", (count, locked_until, user_row["id"]))
    return delay_seconds
