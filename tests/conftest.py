import pytest
from zipfile import ZIP_DEFLATED, ZipFile
from app import create_app


@pytest.fixture()
def app(tmp_path):
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    with ZipFile(downloads / "orbital-drift.zip", "w", ZIP_DEFLATED) as archive:
        archive.writestr("demo.txt", "Synthetic test package")
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
        "DATABASE": str(tmp_path / "test.sqlite3"),
        "SECRET_KEY": "test-secret-key-for-pytest-only",
        "DOWNLOAD_DIR": str(downloads),
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def sign_in(client, username="student", password="Student@12345", code=""):
    return client.post("/login", data={"username": username, "password": password, "totp_code": code}, follow_redirects=False)
