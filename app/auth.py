import re
import secrets
import time
from datetime import datetime, timezone

import pyotp
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user, login_required
from flask_limiter.util import get_remote_address

from . import limiter, secret_box
from .db import get_db, hash_password, log_security_event, update_login_failure, utc_now, verify_password
from .models import User

bp = Blueprint("auth", __name__)


def account_key():
    return (request.form.get("username", "unknown").strip().lower() or "unknown")


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("8 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")
        problems = []
        if not re.fullmatch(r"[A-Za-z0-9_]{3,24}", username):
            problems.append("Use a username with 3–24 letters, numbers, or underscores.")
        if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            problems.append("Enter a valid email address.")
        if not 2 <= len(display_name) <= 60:
            problems.append("Enter a display name with 2–60 characters.")
        if len(password) < 12 or len(password) > 128 or not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password) or not re.search(r"\d", password):
            problems.append("Use 12–128 characters with an uppercase letter, lowercase letter, and number.")
        db = get_db()
        if not problems and db.execute("SELECT 1 FROM users WHERE username=? OR email=?", (username, email)).fetchone():
            problems.append("That username or email is already in use.")
        if problems:
            for problem in problems:
                flash(problem, "error")
        else:
            try:
                cursor = db.execute("INSERT INTO users(username,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?)", (username, email, hash_password(password), display_name, "user", utc_now()))
                user_id = cursor.lastrowid
                db.execute("INSERT INTO user_profiles(user_id,updated_at) VALUES(?,?)", (user_id, utc_now()))
                log_security_event("account_registered", username, user_id=user_id)
                db.commit()
                flash("Account created. Sign in to continue.", "success")
                return redirect(url_for("auth.login"))
            except Exception:
                db.rollback()
                flash("We could not create the account. Check the details and try again.", "error")
    return render_template("auth/register.html")


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("12 per minute")
@limiter.limit("25 per hour", key_func=account_key)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        code = request.form.get("totp_code", "").strip().replace(" ", "")
        captcha_required = int(session.get("login_failures", 0)) >= 3
        captcha_answer = session.get("captcha_answer")
        if captcha_required and (not captcha_answer or request.form.get("captcha_answer", "").strip() != str(captcha_answer)):
            flash("Sign-in failed. Check your details and try again.", "error")
            return render_template("auth/login.html", captcha_required=True, challenge=session.get("captcha_challenge")), 400

        db = get_db()
        row = db.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        now = datetime.now(timezone.utc)
        locked = False
        if row and row["locked_until"]:
            try:
                locked = datetime.fromisoformat(row["locked_until"]) > now
            except ValueError:
                locked = False
        valid = bool(row and row["is_active"] and not locked and verify_password(row["password_hash"], password))
        if valid and row["mfa_enabled"]:
            try:
                encrypted = row["totp_secret"].encode("utf-8")
                secret = secret_box(current_app_from_request()).decrypt(encrypted).decode("utf-8")
                valid = pyotp.TOTP(secret).verify(code, valid_window=1)
            except Exception:
                valid = False
        if not valid:
            if row and locked:
                # A request during an active lock must never clear or shorten it.
                log_security_event("login_failed_locked", username)
                db.commit()
            elif row:
                delay = update_login_failure(row)
                db.commit()
                time.sleep(delay)
            log_security_event("login_failed", username)
            db.commit()
            failures = int(session.get("login_failures", 0)) + 1
            session["login_failures"] = failures
            captcha_required = failures >= 3
            if captcha_required:
                left, right = secrets.randbelow(7) + 2, secrets.randbelow(7) + 2
                session["captcha_answer"] = left + right
                session["captcha_challenge"] = f"{left} + {right}"
            flash("Sign-in failed. Check your details and try again.", "error")
            return render_template("auth/login.html", captcha_required=captcha_required, challenge=session.get("captcha_challenge")), 401

        db.execute("UPDATE users SET failed_login_count=0,locked_until=NULL WHERE id=?", (row["id"],))
        log_security_event("login_success", username, user_id=row["id"])
        db.commit()
        session.clear()  # Rotate the signed session payload at the privilege boundary.
        login_user(User.from_row(row), remember=False, fresh=True)
        session.permanent = True
        return redirect(request.args.get("next") if safe_next(request.args.get("next")) else url_for("main.dashboard"))

    return render_template("auth/login.html", captcha_required=False, challenge=None)


def current_app_from_request():
    from flask import current_app
    return current_app._get_current_object()


def safe_next(target):
    if not target:
        return False
    from urllib.parse import urlparse
    parsed = urlparse(target)
    return not parsed.netloc and target.startswith("/") and not target.startswith("//")


@bp.post("/logout")
@login_required
def logout():
    log_security_event("logout", current_user.username, user_id=current_user.id)
    get_db().commit()
    logout_user()
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("main.index"))


@bp.route("/account/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        bio = request.form.get("bio", "").strip()
        favorite = request.form.get("favorite_genre", "").strip()
        if not 2 <= len(display_name) <= 60 or len(bio) > 300 or len(favorite) > 40:
            flash("Check the profile fields and try again.", "error")
        else:
            db.execute("UPDATE users SET display_name=? WHERE id=?", (display_name, current_user.id))
            db.execute("UPDATE user_profiles SET bio=?,favorite_genre=?,updated_at=? WHERE user_id=?", (bio, favorite, utc_now(), current_user.id))
            log_security_event("profile_updated", current_user.username, user_id=current_user.id)
            db.commit()
            flash("Profile saved.", "success")
            return redirect(url_for("auth.profile"))
    profile = db.execute("SELECT * FROM user_profiles WHERE user_id=?", (current_user.id,)).fetchone()
    return render_template("auth/profile.html", profile=profile)


@bp.route("/account/mfa", methods=["GET", "POST"])
@login_required
def mfa():
    db = get_db()
    if request.method == "POST" and request.form.get("action") == "enable":
        pending = db.execute("SELECT totp_pending FROM users WHERE id=?", (current_user.id,)).fetchone()["totp_pending"]
        code = request.form.get("code", "").strip()
        try:
            secret = secret_box(current_app_from_request()).decrypt(pending.encode()).decode() if pending else ""
        except Exception:
            secret = ""
        if secret and pyotp.TOTP(secret).verify(code, valid_window=1):
            protected = secret_box(current_app_from_request()).encrypt(secret.encode()).decode()
            db.execute("UPDATE users SET totp_secret=?,totp_pending=NULL,mfa_enabled=1 WHERE id=?", (protected, current_user.id))
            log_security_event("mfa_enabled", current_user.username, user_id=current_user.id)
            db.commit()
            flash("MFA is enabled for your account.", "success")
            return redirect(url_for("auth.mfa"))
        flash("That verification code did not match. Try again.", "error")
    elif request.method == "POST" and request.form.get("action") == "disable":
        row = db.execute("SELECT password_hash,totp_secret FROM users WHERE id=?", (current_user.id,)).fetchone()
        code = request.form.get("code", "").strip()
        try:
            secret = secret_box(current_app_from_request()).decrypt(row["totp_secret"].encode()).decode()
            valid_code = pyotp.TOTP(secret).verify(code, valid_window=1)
        except Exception:
            valid_code = False
        if verify_password(row["password_hash"], request.form.get("password", "")) and valid_code:
            db.execute("UPDATE users SET totp_secret=NULL,totp_pending=NULL,mfa_enabled=0 WHERE id=?", (current_user.id,))
            log_security_event("mfa_disabled", current_user.username, user_id=current_user.id)
            db.commit()
            flash("MFA is disabled.", "success")
            return redirect(url_for("auth.mfa"))
        flash("Password or verification code was not accepted.", "error")

    row = db.execute("SELECT mfa_enabled,totp_pending FROM users WHERE id=?", (current_user.id,)).fetchone()
    secret = None
    uri = None
    if not row["mfa_enabled"]:
        if not row["totp_pending"]:
            raw = pyotp.random_base32()
            db.execute("UPDATE users SET totp_pending=? WHERE id=?", (secret_box(current_app_from_request()).encrypt(raw.encode()).decode(), current_user.id))
            db.commit()
            row = db.execute("SELECT mfa_enabled,totp_pending FROM users WHERE id=?", (current_user.id,)).fetchone()
        secret = secret_box(current_app_from_request()).decrypt(row["totp_pending"].encode()).decode()
        uri = pyotp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name="Pixel Vault Training Lab")
    return render_template("auth/mfa.html", enabled=bool(row["mfa_enabled"]), secret=secret, uri=uri)
