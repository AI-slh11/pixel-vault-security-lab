from conftest import sign_in


def test_public_browse_and_search(client):
    assert client.get("/").status_code == 200
    assert client.get("/?q=Orbital").status_code == 200
    assert b"Orbital Drift" in client.get("/?q=Orbital").data
    assert client.get("/games/orbital-drift").status_code == 200


def test_regular_pages_require_login(client):
    assert client.get("/dashboard").status_code == 302
    assert client.get("/my-downloads").status_code == 302
    assert client.post("/games/orbital-drift/download").status_code == 302


def test_isolated_vulnerable_member_endpoint_and_secure_comparison(client):
    exposed = client.get("/lab/vulnerable/member-download")
    assert exposed.status_code == 200 and exposed.json["access"] == "granted"
    assert exposed.json["record"] == "LAB-MEMBER-001"
    assert client.get("/lab/secure/member-download").status_code == 401
    sign_in(client)
    assert client.get("/lab/secure/member-download").json["account"] == "student"


def test_isolated_admin_escalation_and_secure_comparison(client):
    exposed = client.get("/lab/vulnerable/admin-report")
    assert exposed.status_code == 200 and exposed.json["synthetic"] is True
    assert client.get("/lab/secure/admin-report").status_code == 401
    assert client.get("/admin/").status_code == 302
    sign_in(client)
    assert client.get("/lab/secure/admin-report").status_code == 403
    assert client.get("/admin/").status_code == 403
    client.post("/logout")
    sign_in(client, "admin", "Admin@12345")
    assert client.get("/lab/secure/admin-report").status_code == 200
    assert client.get("/admin/").status_code == 200


def test_download_is_account_scoped_and_stored(client, app):
    sign_in(client)
    response = client.post("/games/orbital-drift/download")
    assert response.status_code == 200
    assert response.data[:2] == b"PK"
    assert client.get("/my-downloads").status_code == 200
    with app.app_context():
        from app.db import get_db
        count = get_db().execute("SELECT COUNT(*) AS n FROM downloads WHERE user_id=(SELECT id FROM users WHERE username='student')").fetchone()["n"]
        assert count == 1


def test_player_history_does_not_include_another_users_downloads(client):
    sign_in(client)
    client.post("/games/orbital-drift/download")
    client.post("/logout")
    sign_in(client, "admin", "Admin@12345")
    assert b"Orbital Drift" not in client.get("/my-downloads").data


def test_admin_can_manage_categories_but_player_cannot(client):
    sign_in(client)
    assert client.get("/admin/categories").status_code == 403
    client.post("/logout")
    sign_in(client, "admin", "Admin@12345")
    response = client.post("/admin/categories", data={"name": "Exploration"})
    assert response.status_code == 302
    from app.db import get_db
    with client.application.app_context():
        category = get_db().execute("SELECT id FROM categories WHERE slug='exploration'").fetchone()
        assert category
    assert client.post(f"/admin/categories/{category['id']}/edit", data={"name": "Exploration Plus"}).status_code == 302
    with client.application.app_context():
        assert get_db().execute("SELECT id FROM categories WHERE slug='exploration-plus'").fetchone()
    assert client.post(f"/admin/categories/{category['id']}/delete").status_code == 302
