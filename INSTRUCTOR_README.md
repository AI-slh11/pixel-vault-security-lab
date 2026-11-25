# Instructor-only access-control lab notes

**Keep this file private. It is not linked from the site and is outside `app/`, the directory served by Flask.** The site UI describes only practice and protected modes; it does not name the vulnerability classes.

The project intentionally contains exactly two vulnerable access-control endpoints. Each returns fixed fictional training content, is isolated in `app/lab.py`, and is separate from authentication, the SQLite user data, game-download delivery, and real administrator functions. The corresponding protected handlers are distinct routes. Do not add real user, account, file, or administrator data to these handlers.

## Vulnerability 1 — Unauthenticated Access Control Bypass

- **Concept:** a guest can invoke a server-side feature intended for a registered player.
- **Root cause:** the practice handler intentionally has no authentication decorator or user check.
- **Affected endpoint:** `GET /lab/vulnerable/member-download`.
- **Synthetic response:** hardcoded fictional member feature, fictional game name, and lab record `LAB-MEMBER-001`. It does not return a real file or read user rows.
- **Expected secure behavior:** an anonymous request should be redirected to sign-in or rejected with `401`. `GET /lab/secure/member-download` uses Flask-Login's `@login_required` and returns only after a valid local session exists.
- **Comparison:** call both member endpoints while signed out, then sign in as `student` and repeat. The practice endpoint responds without identity; the protected endpoint requires a session.
- **Educational objectives:** identify the missing server-side access check, distinguish interface hiding from endpoint enforcement, and observe how the server response changes after authentication is applied.
- **Remediation:** enforce authentication at the server route or service layer for every registered-user feature. Treat UI controls as presentation only and test direct endpoint requests as a guest.

## Vulnerability 2 — Vertical Privilege Escalation

- **Concept:** an ordinary registered player can invoke a feature intended only for an administrator.
- **Root cause:** the practice handler intentionally omits the server-side role authorization decorator.
- **Affected endpoint:** `GET /lab/vulnerable/admin-report`.
- **Synthetic response:** fixed fictional catalog counts; it does not query real analytics, users, or administrator data.
- **Expected secure behavior:** an anonymous request should be redirected to sign-in; a signed-in non-admin should receive `403`; an administrator may receive the feature response. `GET /lab/secure/admin-report` applies `@admin_required`, which checks the authenticated user's database-backed role.
- **Comparison:** call both admin endpoints signed out, then as `student`, then as `admin`. The practice route responds in each case; the protected route denies the first two and allows the last.
- **Educational objectives:** distinguish authentication (who is signed in) from authorization (which role is allowed), test server routes directly, and verify that role checks are enforced on the server.
- **Remediation:** require a verified administrator role at every privileged route and service operation. Keep role assignment server-controlled and test with a regular user, not only an administrator.

## Lab endpoint map

| Practice endpoint | Protected comparison | Expected protected behavior |
|---|---|---|
| `GET /lab/vulnerable/member-download` | `GET /lab/secure/member-download` | Sign-in required |
| `GET /lab/vulnerable/admin-report` | `GET /lab/secure/admin-report` | Admin role required |

No IDOR, authentication bypass, weak password verifier, or real-data exposure is part of these exercises. The login and account system is intended to remain secure in both UI modes.

## Demo credentials

For local training only: `student` / `Student@12345` and `admin` / `Admin@12345`. These are deliberately disclosed demo credentials and **must never be reused** on another system. Passwords are seeded as Argon2id hashes in the local SQLite database.
