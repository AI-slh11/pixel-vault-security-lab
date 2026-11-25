import re
from datetime import datetime, timedelta, timezone

import pyotp

from app.db import get_db, verify_password
from conftest import sign_in


def test_seed_passwords_are_argon2id_hashes(client, app):
    with app.app_context():
        rows = get_db().execute("SELECT username,password_hash FROM users").fetchall()
        assert {row["username"] for row in rows} == {"student", "admin"}
        assert all(row["password_hash"].startswith("$argon2id$") for row in rows)
        assert verify_password(next(row["password_hash"] for row in rows if row["username"] == "student"), "Student@12345")


def test_login_logout_and_session_cookie(client):
    response = sign_in(client)
    assert response.status_code == 302
    cookie = response.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie
    assert client.get("/dashboard").status_code == 200
    assert client.post("/logout").status_code == 302
    assert client.get("/dashboard").status_code == 302


def test_login_error_is_generic(client):
    response = client.post("/login", data={"username": "student", "password": "wrong-password"})
    assert response.status_code == 401
    assert b"Sign-in failed. Check your details" in response.data
    assert b"No account exists" not in response.data


def test_captcha_is_required_after_suspicious_failures(client):
    with client.session_transaction() as session:
        session["login_failures"] = 3
        session["captcha_answer"] = 8
        session["captcha_challenge"] = "3 + 5"
    response = client.post("/login", data={"username": "student", "password": "Student@12345"})
    assert response.status_code == 400
    assert b"Quick human check" in response.data


def test_active_account_lockout_survives_login_attempts(client, app):
    locked_until = (datetime.now(timezone.utc) + timedelta(minutes=8)).isoformat()
    with app.app_context():
        from app.db import get_db
        get_db().execute("UPDATE users SET failed_login_count=0,locked_until=? WHERE username='student'", (locked_until,))
        get_db().commit()
    response = client.post("/login", data={"username": "student", "password": "Student@12345"})
    assert response.status_code == 401
    with app.app_context():
        from app.db import get_db
        saved = get_db().execute("SELECT locked_until FROM users WHERE username='student'").fetchone()["locked_until"]
        assert saved == locked_until


def test_registration_and_password_validation(client, app):
    bad = client.post("/register", data={"username": "newplayer", "email": "new@example.test", "display_name": "New Player", "password": "short"})
    assert b"12\xe2\x80\x93128 characters" in bad.data
    good = client.post("/register", data={"username": "newplayer", "email": "new@example.test", "display_name": "New Player", "password": "StrongPass123"})
    assert good.status_code == 302
    with app.app_context():
        row = get_db().execute("SELECT password_hash FROM users WHERE username='newplayer'").fetchone()
        assert row["password_hash"].startswith("$argon2id$")


def test_mfa_setup_and_login(client):
    sign_in(client)
    page = client.get("/account/mfa")
    match = re.search(rb'class="totp-secret">([A-Z2-7]+)</code>', page.data)
    assert match
    secret = match.group(1).decode()
    code = pyotp.TOTP(secret).now()
    enabled = client.post("/account/mfa", data={"action": "enable", "code": code})
    assert enabled.status_code == 302
    client.post("/logout")
    assert client.post("/login", data={"username": "student", "password": "Student@12345"}).status_code == 401
    assert sign_in(client, code=pyotp.TOTP(secret).now()).status_code == 302
