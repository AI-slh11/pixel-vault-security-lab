# Security testing checklist

Run locally with `python -m pytest -q` and the test server bound to `127.0.0.1`.

## Authentication

- [ ] Verify stored password hashes use Argon2id and no plaintext passwords exist in SQLite.
- [ ] Verify generic login failures for existing and nonexistent usernames.
- [ ] Exercise per-IP and per-account throttling; confirm progressive delays and temporary lockout.
- [ ] Verify the human challenge appears after repeated suspicious login attempts.
- [ ] Verify HTTP-only, SameSite cookies, session replacement after successful login, expiry, and logout.
- [ ] Verify CSRF tokens on every state-changing form and rejection when absent/invalid.
- [ ] Enroll and validate TOTP MFA; reject invalid codes; require password and code to disable MFA.
- [ ] Review the security event log; confirm passwords and authenticator codes are never recorded.

## Access control

- [ ] Guest may browse/search catalog and view game details.
- [ ] Guest is redirected from dashboard, profile, downloads, and download history.
- [ ] A player can read/edit only their own profile and download history.
- [ ] A player receives `403` from real admin dashboards and management actions.
- [ ] An administrator can view statistics and manage games, categories, and player status.
- [ ] Verify the isolated member-feature practice endpoint responds to a guest; verify its protected comparison denies the guest.
- [ ] Verify the isolated admin-feature practice endpoint responds to guest/player; verify its protected comparison denies guest and player but allows admin.
- [ ] Confirm the instructor notes stay outside the Flask-served `app/` tree.

## Application and local isolation

- [ ] Try malformed, oversized, and duplicate registration/profile/game inputs.
- [ ] Verify errors do not include stack traces or secrets.
- [ ] Confirm downloaded ZIPs are original harmless demo games and the user history is recorded.
- [ ] Confirm user history and admin statistics are derived from the correct SQLite rows.
- [ ] Confirm foreign-key enforcement, security headers, and no-store headers for authenticated pages.
- [ ] Confirm only loopback is bound; do not use network forwarding or public hosting.
