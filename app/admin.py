import re

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .db import get_db, log_security_event, utc_now

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    from functools import wraps
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@bp.get("/")
@admin_required
def dashboard():
    db = get_db()
    stats = {
        "users": db.execute("SELECT COUNT(*) AS n FROM users WHERE role='user'").fetchone()["n"],
        "games": db.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"],
        "downloads": db.execute("SELECT COUNT(*) AS n FROM downloads").fetchone()["n"],
        "categories": db.execute("SELECT COUNT(*) AS n FROM categories").fetchone()["n"],
    }
    events = db.execute("SELECT * FROM security_logs ORDER BY id DESC LIMIT 12").fetchall()
    return render_template("admin/dashboard.html", stats=stats, events=events)


@bp.route("/games", methods=["GET", "POST"])
@admin_required
def games():
    db = get_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category_id = request.form.get("category_id", "")
        description = request.form.get("description", "").strip()
        difficulty = request.form.get("difficulty", "Standard").strip()[:30]
        accent = request.form.get("accent", "#46d6c5").strip()
        sample_slug = request.form.get("sample_slug", "orbital-drift")
        if not 2 <= len(title) <= 80 or len(description) > 500 or not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
            flash("Check the game title, description, and accent color.", "error")
        elif sample_slug not in {"orbital-drift", "signal-garden", "tiny-kingdoms", "pixel-sprint"}:
            flash("Choose one of the included sample packages.", "error")
        elif not db.execute("SELECT id FROM categories WHERE id=?", (category_id,)).fetchone():
            flash("Choose a valid category.", "error")
        else:
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:70]
            try:
                db.execute("INSERT INTO games(slug,title,category_id,description,difficulty,file_path,rating,accent,artwork_slug,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (slug, title, int(category_id), description, difficulty, f"app/static/downloads/{sample_slug}.zip", "New", accent, sample_slug, utc_now()))
                log_security_event("admin_game_created", current_user.username, slug, user_id=current_user.id)
                db.commit()
                flash("Game added to the catalog.", "success")
                return redirect(url_for("admin.games"))
            except Exception:
                db.rollback()
                flash("Could not add that game. Check that its title is unique.", "error")
    games = db.execute("SELECT g.*,c.name AS category_name FROM games g JOIN categories c ON c.id=g.category_id ORDER BY g.title").fetchall()
    categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return render_template("admin/games.html", games=games, categories=categories)


@bp.post("/games/<int:game_id>/edit")
@admin_required
def edit_game(game_id):
    db = get_db()
    game = db.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
    if not game:
        abort(404)
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category_id = request.form.get("category_id", "")
    sample_slug = request.form.get("sample_slug", "orbital-drift")
    if not 2 <= len(title) <= 80 or len(description) > 500 or sample_slug not in {"orbital-drift", "signal-garden", "tiny-kingdoms", "pixel-sprint"} or not db.execute("SELECT id FROM categories WHERE id=?", (category_id,)).fetchone():
        flash("Check the game details and category.", "error")
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:70]
        try:
            db.execute("UPDATE games SET slug=?,title=?,description=?,category_id=?,difficulty=?,file_path=?,artwork_slug=? WHERE id=?", (slug, title, description, int(category_id), request.form.get("difficulty", "Standard")[:30], f"app/static/downloads/{sample_slug}.zip", sample_slug, game_id))
            log_security_event("admin_game_updated", current_user.username, slug, user_id=current_user.id)
            db.commit()
            flash("Game updated.", "success")
        except Exception:
            db.rollback()
            flash("That title is already used by another game.", "error")
    return redirect(url_for("admin.games"))


@bp.post("/games/<int:game_id>/delete")
@admin_required
def delete_game(game_id):
    db = get_db()
    game = db.execute("SELECT title FROM games WHERE id=?", (game_id,)).fetchone()
    if not game:
        abort(404)
    db.execute("DELETE FROM downloads WHERE game_id=?", (game_id,))
    db.execute("DELETE FROM games WHERE id=?", (game_id,))
    log_security_event("admin_game_deleted", current_user.username, game["title"], user_id=current_user.id)
    db.commit()
    flash("Game removed.", "success")
    return redirect(url_for("admin.games"))


@bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
        if not 2 <= len(name) <= 40 or not slug:
            flash("Enter a category name with 2–40 characters.", "error")
        else:
            try:
                db.execute("INSERT INTO categories(name,slug) VALUES(?,?)", (name, slug))
                db.commit()
                flash("Category added.", "success")
                return redirect(url_for("admin.categories"))
            except Exception:
                flash("That category already exists.", "error")
    categories = db.execute("SELECT c.*,COUNT(g.id) AS game_count FROM categories c LEFT JOIN games g ON g.category_id=c.id GROUP BY c.id ORDER BY c.name").fetchall()
    return render_template("admin/categories.html", categories=categories)


@bp.post("/categories/<int:category_id>/delete")
@admin_required
def delete_category(category_id):
    db = get_db()
    category = db.execute("SELECT name FROM categories WHERE id=?", (category_id,)).fetchone()
    if not category:
        abort(404)
    used = db.execute("SELECT 1 FROM games WHERE category_id=? LIMIT 1", (category_id,)).fetchone()
    if used:
        flash("Move or remove this category’s games before deleting it.", "error")
    else:
        db.execute("DELETE FROM categories WHERE id=?", (category_id,))
        log_security_event("admin_category_deleted", current_user.username, category["name"], user_id=current_user.id)
        db.commit()
        flash("Category removed.", "success")
    return redirect(url_for("admin.categories"))


@bp.post("/categories/<int:category_id>/edit")
@admin_required
def edit_category(category_id):
    db = get_db()
    old = db.execute("SELECT name FROM categories WHERE id=?", (category_id,)).fetchone()
    if not old:
        abort(404)
    name = request.form.get("name", "").strip()
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
    if not 2 <= len(name) <= 40 or not slug:
        flash("Enter a category name with 2–40 characters.", "error")
    else:
        try:
            db.execute("UPDATE categories SET name=?,slug=? WHERE id=?", (name, slug, category_id))
            log_security_event("admin_category_updated", current_user.username, name, user_id=current_user.id)
            db.commit()
            flash("Category updated.", "success")
        except Exception:
            db.rollback()
            flash("That category name is already in use.", "error")
    return redirect(url_for("admin.categories"))


@bp.get("/users")
@admin_required
def users():
    rows = get_db().execute("SELECT u.id,u.username,u.email,u.display_name,u.is_active,u.created_at,COUNT(d.id) AS downloads FROM users u LEFT JOIN downloads d ON d.user_id=u.id WHERE u.role='user' GROUP BY u.id ORDER BY u.created_at DESC").fetchall()
    return render_template("admin/users.html", users=rows)


@bp.post("/users/<int:user_id>/toggle")
@admin_required
def toggle_user(user_id):
    db = get_db()
    row = db.execute("SELECT username,is_active FROM users WHERE id=? AND role='user'", (user_id,)).fetchone()
    if not row:
        abort(404)
    active = 0 if row["is_active"] else 1
    db.execute("UPDATE users SET is_active=? WHERE id=?", (active, user_id))
    log_security_event("admin_user_status_changed", current_user.username, row["username"], user_id=current_user.id)
    db.commit()
    flash("Account status updated.", "success")
    return redirect(url_for("admin.users"))
