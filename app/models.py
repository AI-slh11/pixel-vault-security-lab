from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, row):
        self.id = str(row["id"])
        self.username = row["username"]
        self.email = row["email"]
        self.role = row["role"]
        self.display_name = row["display_name"]
        self._active = bool(row["is_active"])
        self.mfa_enabled = bool(row["mfa_enabled"])
        self.password_hash = row["password_hash"]
        self.locked_until = row["locked_until"]
        self.failed_login_count = row["failed_login_count"]
        self.totp_secret = row["totp_secret"]
        self.totp_pending = row["totp_pending"]

    @classmethod
    def from_row(cls, row):
        return cls(row) if row else None

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_active(self):
        return self._active
