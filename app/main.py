import re
from pathlib import Path

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from .db import get_db, log_security_event, utc_now

bp = Blueprint("main", __name__)


@bp.app_context_processor
def global_template_data():
    db = get_db()
    categories = db.execute("SELECT id,name,slug FROM categories ORDER BY name").fetchall()
    return {"nav_categories": categories}


@bp.get("/")
def index():
    db = get_db()
    query = request.args.get("q", "").strip()[:80]
    category = request.args.get("category", "").strip()[:40]
    conditions = []
    params = []
    if query:
        pattern = f"%{query}%"
        conditions.append("(g.title LIKE ? OR g.description LIKE ? OR c.name LIKE ?)")
        params.extend([pattern, pattern, pattern])
    if category:
        conditions.append("c.slug = ?")
        params.append(category)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    games = db.execute(f"SELECT g.*,c.name AS category_name,c.slug AS category_slug FROM games g JOIN categories c ON c.id=g.category_id {where} ORDER BY g.id", params).fetchall()
    categories = db.execute("SELECT c.*,COUNT(g.id) AS game_count FROM categories c LEFT JOIN games g ON g.category_id=c.id GROUP BY c.id ORDER BY c.name").fetchall()
    return render_template("home.html", games=games, categories=categories, query=query, selected_category=category)


@bp.get("/games/<slug>")
def game_detail(slug):
    game = get_db().execute("SELECT g.*,c.name AS category_name,c.slug AS category_slug FROM games g JOIN categories c ON c.id=g.category_id WHERE g.slug=?", (slug,)).fetchone()
    if not game:
        abort(404)
    return render_template("game_detail.html", game=game)


@bp.post("/games/<slug>/download")
@login_required
def download_game(slug):
    db = get_db()
    game = db.execute("SELECT * FROM games WHERE slug=?", (slug,)).fetchone()
    if not game:
        abort(404)
    download_root = Path(current_app.config["DOWNLOAD_DIR"]).resolve()
    path = (download_root / Path(game["file_path"]).name).resolve()
    if not path.is_relative_to(download_root) or not path.is_file():
        abort(404)
    db.execute("INSERT INTO downloads(user_id,game_id,downloaded_at) VALUES(?,?,?)", (current_user.id, game["id"], utc_now()))
    log_security_event("game_download", current_user.username, game["slug"], user_id=current_user.id)
    db.commit()
    return send_file(path, as_attachment=True, download_name=f"{game['slug']}.zip", mimetype="application/zip", max_age=0)


@bp.get("/dashboard")
@login_required
def dashboard():
    db = get_db()
    recent = db.execute("SELECT d.downloaded_at,g.title,g.slug,g.accent,g.artwork_slug FROM downloads d JOIN games g ON g.id=d.game_id WHERE d.user_id=? ORDER BY d.downloaded_at DESC LIMIT 5", (current_user.id,)).fetchall()
    count = db.execute("SELECT COUNT(*) AS n FROM downloads WHERE user_id=?", (current_user.id,)).fetchone()["n"]
    games = db.execute("SELECT slug,title,accent,artwork_slug FROM games ORDER BY id LIMIT 4").fetchall()
    return render_template("dashboard.html", recent=recent, download_count=count, featured_games=games)


@bp.get("/my-downloads")
@login_required
def my_downloads():
    downloads = get_db().execute("SELECT d.downloaded_at,g.title,g.slug,g.accent,g.description FROM downloads d JOIN games g ON g.id=d.game_id WHERE d.user_id=? ORDER BY d.downloaded_at DESC", (current_user.id,)).fetchall()
    return render_template("downloads.html", downloads=downloads)


@bp.get("/training-lab")
def training_lab():
    mode = "secure" if request.args.get("mode") == "secure" else "vulnerable"
    return render_template("lab.html", mode=mode)
