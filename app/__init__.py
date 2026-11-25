import hashlib
import os
from base64 import urlsafe_b64encode
from pathlib import Path

from cryptography.fernet import Fernet
from flask import Flask, jsonify, render_template, request
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFError, CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from .db import get_db, initialize_database, initialize_d1
from .models import User

login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)


def _secret_key(instance_path: Path) -> str:
    configured = os.environ.get("FLASK_SECRET_KEY")
    if configured:
        return configured
    key_file = instance_path / "secret.key"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()
    key = urlsafe_b64encode(os.urandom(48)).decode("ascii")
    key_file.write_text(key, encoding="utf-8")
    try:
        key_file.chmod(0o600)
    except OSError:
        pass
    return key


def secret_box(app: Flask) -> Fernet:
    digest = hashlib.sha256(app.secret_key.encode("utf-8")).digest()
    return Fernet(urlsafe_b64encode(digest))


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    app.config["D1_DATABASE"] = app.config.get("D1_DATABASE") or os.environ.get("CLOUDFLARE_D1_BINDING")
    app.config["PUBLIC_DEPLOYMENT"] = os.environ.get("PUBLIC_DEPLOYMENT", "false").lower() == "true"
    d1_mode = app.config.get("D1_DATABASE") is not None
    if not d1_mode:
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config.get("SECRET_KEY"):
        app.secret_key = _secret_key(Path(app.instance_path)) if not d1_mode else os.environ.get("FLASK_SECRET_KEY", "")
    if test_config:
        app.config.update(test_config)
    if not d1_mode:
        Path(app.config["DOWNLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Sign in to continue."
    login_manager.login_message_category = "info"
    csrf.init_app(app)
    limiter.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        row = get_db().execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,)).fetchone()
        return User.from_row(row) if row else None

    from .auth import bp as auth_bp
    from .main import bp as main_bp
    from .admin import bp as admin_bp
    from .lab import bp as lab_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(lab_bp)

    @app.before_request
    def disable_public_training_exploits():
        if app.config.get("PUBLIC_DEPLOYMENT") and request.path.startswith("/lab/vulnerable/"):
            from flask import abort
            abort(404)

    @app.before_request
    def refresh_session_lifetime():
        from flask import session
        if current_user.is_authenticated:
            session.permanent = True

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
        if current_user.is_authenticated:
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        if request.accept_mimetypes.best == "application/json":
            return jsonify(error="The form expired. Reload and try again."), 400
        return render_template("error.html", code=400, message="This form expired or could not be verified. Reload the page and try again."), 400

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="That page is not in the game library."), 404

    @app.errorhandler(429)
    def too_many_requests(_error):
        return render_template("error.html", code=429, message="Too many requests. Wait a little and try again."), 429

    with app.app_context():
        if app.config.get("D1_DATABASE") is None:
            initialize_database(app)

    return app


def create_worker_app(env):
    """Create the Cloudflare Worker app with its D1 binding and secret."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    app.config.update(
        SECRET_KEY=env.FLASK_SECRET_KEY,
        D1_DATABASE=env.DB,
        PUBLIC_DEPLOYMENT=True,
        SESSION_COOKIE_SECURE=True,
        DOWNLOAD_DIR=str(Path(__file__).parent / "static" / "downloads"),
    )
    app.secret_key = env.FLASK_SECRET_KEY
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Sign in to continue."
    csrf.init_app(app)
    limiter.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        row = get_db().execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,)).fetchone()
        return User.from_row(row) if row else None

    from .auth import bp as auth_bp
    from .main import bp as main_bp
    from .admin import bp as admin_bp
    from .lab import bp as lab_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(lab_bp)

    @app.before_request
    def public_lab_route_guard():
        if request.path.startswith("/lab/vulnerable/"):
            from flask import abort
            abort(404)
        from flask import session
        if current_user.is_authenticated:
            session.permanent = True

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
        if current_user.is_authenticated:
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        if request.accept_mimetypes.best == "application/json":
            return jsonify(error="The form expired. Reload and try again."), 400
        return render_template("error.html", code=400, message="This form expired or could not be verified. Reload the page and try again."), 400

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="That page is not in the game library."), 404

    @app.errorhandler(429)
    def too_many_requests(_error):
        return render_template("error.html", code=429, message="Too many requests. Wait a little and try again."), 429

    return app
