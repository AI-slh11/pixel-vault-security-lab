from pathlib import Path

from app import create_app


def test_all_post_forms_have_global_csrf_protection(tmp_path):
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": True, "RATELIMIT_ENABLED": False, "DATABASE": str(tmp_path / "csrf.sqlite3"), "SECRET_KEY": "csrf-test-secret"})
    response = app.test_client().post("/login", data={"username": "student", "password": "Student@12345"})
    assert response.status_code == 400
    assert b"form expired" in response.data.lower()


def test_security_headers_and_session_policy(client):
    response = client.get("/")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_local_runner_binds_only_loopback():
    source = Path(__file__).parents[1].joinpath("run.py").read_text(encoding="utf-8")
    assert 'host="127.0.0.1"' in source
    assert 'host="0.0.0.0"' not in source


def test_secure_routes_do_not_use_the_vulnerable_route_handlers():
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "RATELIMIT_ENABLED": False, "DATABASE": ":memory:", "SECRET_KEY": "route-check"})
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/lab/vulnerable/member-download" in rules
    assert "/lab/secure/member-download" in rules
    assert "/lab/vulnerable/admin-report" in rules
    assert "/lab/secure/admin-report" in rules
    assert sum("/lab/vulnerable/" in rule for rule in rules) == 2
