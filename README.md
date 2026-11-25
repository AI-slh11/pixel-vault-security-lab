# Pixel Vault — Gaming Download & Security Training Lab

## Cloudflare hosted edition

The public Cloudflare edition is available at <https://pixel-vault-training-lab.serveflow-havox.workers.dev>. It serves a read-only synthetic game catalog and sample downloads backed by a dedicated Cloudflare D1 database. Public API routes under `/lab/vulnerable/` and `/api/lab/vulnerable/` return 404. The hosted guide is informational; registration, login, account management, administrator tools, and the working access-control exercises remain in the local Flask application described below. Do not treat the hosted preview as a production account system.

Pixel Vault is a gaming catalog and web application security training lab built with Python 3, Flask, and SQLite. The full local app includes original, harmless downloadable mini-games, player accounts, an administrator workspace, and two separated modes for access-control practice. The hosted Cloudflare edition is a limited public catalog and training guide.

The full Flask training app binds to `127.0.0.1:5000` only. Keep its intentionally vulnerable routes local. The hosted edition serves fictional catalog data and blocks those routes. Both editions use synthetic records only.

## Features

- Dark, responsive game discovery site with search, genre filters, game details, and original artwork.
- Four offline demo game ZIP packages generated locally from source by `make_samples.py`.
- Registration, login, profile editing, personal download history, and account dashboard.
- Administrator dashboard with catalog CRUD, category management, player account controls, statistics, and security-event history.
- Argon2id password hashing, generic login failures, per-IP and per-account rate limits, progressive delays, temporary lockout, and a simple CAPTCHA challenge after repeated failures.
- HTTP-only, SameSite session cookies, 30-minute session lifetime, CSRF protection, session replacement on login, secure logout, and TOTP MFA support. TOTP secrets are encrypted at rest using a key derived from the local Flask secret.
- Isolated training interface at `/training-lab` with practice and protected modes. The endpoints use only synthetic content and are separate from account and administration functions.
- Security headers and server-side role checks for every real administrator page and action.

## Demo accounts

| Role | Username | Password |
|---|---|---|
| Registered player | `student` | `Student@12345` |
| Administrator | `admin` | `Admin@12345` |

These are public training credentials. **Never reuse them, or any password from this project, on another system.** Use synthetic information only. The local SQLite database is created in `instance/` and is excluded from version control.

## Kali Linux installation

Open a terminal in Kali Linux. These instructions assume you have copied or unpacked the `gaming-download-lab` project folder into your home directory.

1. Check Python 3:

   ```bash
   python3 --version
   ```

   Python 3.10 or newer is recommended.

2. Install Python, virtual environment, and native build prerequisites:

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip build-essential libffi-dev libssl-dev
   ```

3. Extract the project ZIP into `~/projects`, then move into the project directory:

   ```bash
   mkdir -p ~/projects
   python3 -m zipfile -e ~/Downloads/gaming-download-lab-source.zip ~/projects
   cd ~/projects/gaming-download-lab
   ```

   If you already extracted the project folder, just `cd` into its location instead.

4. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   ```

5. Activate it:

   ```bash
   source .venv/bin/activate
   ```

   Your terminal prompt should now show `(.venv)`.

6. Install the application packages:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

7. Generate the original game packages and artwork:

   ```bash
   python make_samples.py
   ```

8. Initialize SQLite and create the demo accounts:

   ```bash
   python init_db.py
   ```

   This creates `instance/gaming_lab.sqlite3` and a local secret key. The database and key stay on this computer.

9. Start the local development server:

   ```bash
   python run.py
   ```

   The server prints a local address and listens only on loopback (`127.0.0.1`). Keep this terminal open while using the app.

10. Open the site in a browser at [http://127.0.0.1:5000](http://127.0.0.1:5000). Use the demo accounts above to exercise player and admin workflows. Open `/training-lab` to use the isolated practice interface.

   Browse or search games as a guest. Create an account or sign in as `student` to open the player dashboard and download a game. Unzip a downloaded package and open its `index.html` file in a browser to play offline. Sign in as `admin` to open the **Admin** workspace, where games, categories, and player account status can be managed.

11. Stop the server with **Ctrl+C** in the terminal.

12. When finished, leave the virtual environment with:

   ```bash
   deactivate
   ```

### Troubleshooting

- **`python3: command not found`:** run `sudo apt update && sudo apt install python3 python3-venv python3-pip`.
- **`No module named flask` or another package:** activate `.venv` and run `python -m pip install -r requirements.txt` again.
- **The database does not exist:** run `python make_samples.py` followed by `python init_db.py` from the project directory.
- **Port 5000 is already in use:** stop the other local Flask process first. Do not bind this lab to a network interface.
- **The browser cannot connect:** verify the server is running and visit the exact loopback address `http://127.0.0.1:5000`.
- **MFA was enabled but its setup key is no longer readable:** the key is encrypted with `instance/secret.key`. Restore that local file with the database or disable MFA before replacing it.
- **A download returns 404:** generate the sample packages with `python make_samples.py` and restart the app.

## Project structure

```text
gaming-download-lab/
├── app/
│   ├── admin.py             # Real admin-only functions
│   ├── auth.py              # Registration, login, profile, MFA
│   ├── db.py                # SQLite, Argon2id, audit helpers
│   ├── lab.py               # Isolated access-control training endpoints
│   ├── main.py              # Public catalog, dashboard, downloads
│   ├── models.py
│   ├── schema.sql
│   ├── static/              # Local CSS, JS, artwork, game packages
│   └── templates/
├── instance/                # Local database and signing/encryption key
├── tests/
├── config.py
├── init_db.py
├── make_samples.py
├── requirements.txt
├── run.py
├── README.md
└── INSTRUCTOR_README.md     # Keep private; not served by Flask
```

## Run checks

```bash
python -m pytest -q
```

The tests cover account hashing, login and session behavior, MFA, guest/member/admin permissions, both isolated training modes, download history, CSRF, security headers, and the loopback-only runner.

The HTTP-only and SameSite protections are enabled for the local server. The `Secure` cookie flag is off because the documented development server uses plain HTTP on loopback; set `COOKIE_SECURE=true` if you configure HTTPS locally. Do not expose the HTTP server outside loopback.

## Security checklist

- [ ] Confirm passwords are stored as `$argon2id$` hashes, never plaintext.
- [ ] Verify invalid login responses use the same generic message for unknown users and wrong passwords.
- [ ] Check per-IP and per-account throttling, progressive delay, post-failure CAPTCHA, and temporary lockout.
- [ ] Confirm session cookies are HTTP-only and SameSite=Lax; confirm the session changes after login and ends on logout.
- [ ] Confirm every state-changing HTML form rejects requests without a valid CSRF token.
- [ ] Enroll TOTP MFA, sign in with a valid code, reject an invalid code, and test disabling MFA with password plus code.
- [ ] Browse public game pages as a guest; verify dashboards, history, downloads, and profile require sign-in.
- [ ] Confirm a player can access only their own profile and download history.
- [ ] Confirm a player is denied all real `/admin/` routes and admin actions; confirm the administrator can manage games, categories, and player accounts.
- [ ] In `/training-lab`, compare the two fictional access-control exercises in practice and protected modes. These are the only intentionally vulnerable behaviors.
- [ ] Confirm security events record authentication and admin actions without storing passwords or MFA codes.
- [ ] Confirm generated download ZIPs contain only original HTML game demos and no third-party commercial assets.
- [ ] Confirm the app listens only on `127.0.0.1` and the training lab is not reachable from another device.

## Notes

The built-in demo passwords are intentionally documented for training and must not be reused. The full Flask application and its vulnerable practice endpoints are for local training only. The Cloudflare Worker is a separate limited public demo; it does not expose the intentionally vulnerable endpoints or provide real user accounts.

## Cloudflare deployment

The Worker and D1 database are configured in `wrangler.jsonc`. Install Node.js, then from this folder run:

```bash
npm install
npm run deploy
```

The Worker reads the synthetic catalog from D1 and game assets from the static asset binding. Public routes under `/lab/vulnerable/` return 404. The full vulnerable and secure lab remains available in the local Flask app.
