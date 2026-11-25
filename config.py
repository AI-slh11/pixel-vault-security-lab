import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or ""
    DATABASE = os.environ.get("GAMING_LAB_DATABASE", str(BASE_DIR / "instance" / "gaming_lab.sqlite3"))
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # The documented local HTTP loopback server cannot use Secure cookies. Set
    # COOKIE_SECURE=true if the local server is later placed behind HTTPS.
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_HEADERS_ENABLED = True
    MAX_CONTENT_LENGTH = 1024 * 1024
    DOWNLOAD_DIR = str(BASE_DIR / "app" / "static" / "downloads")
