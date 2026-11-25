from flask import Blueprint, jsonify
from flask_login import current_user

bp = Blueprint("lab", __name__, url_prefix="/lab")


@bp.get("/vulnerable/member-download")
def vulnerable_member_download():
    # INTENTIONAL LAB VULNERABILITY 1: missing login_required. Hardcoded synthetic data only.
    return jsonify({"access": "granted", "feature": "members-only-download", "game": "Starfall Circuit (synthetic)", "download": "synthetic-demo-package", "record": "LAB-MEMBER-001"})


@bp.get("/secure/member-download")
def secure_member_download():
    if not current_user.is_authenticated:
        return jsonify(error="Authentication required"), 401
    return jsonify({"access": "granted", "feature": "members-only-download", "account": current_user.username, "game": "Starfall Circuit (synthetic)", "download": "synthetic-demo-package"})


@bp.get("/vulnerable/admin-report")
def vulnerable_admin_report():
    # INTENTIONAL LAB VULNERABILITY 2: missing admin_required. The report is fictional.
    return jsonify({"access": "granted", "feature": "admin-report", "synthetic": True, "catalog": {"demo-games": 4, "demo-downloads": 128}, "note": "Fictional training metrics; no real account or admin data."})


@bp.get("/secure/admin-report")
def secure_admin_report():
    if not current_user.is_authenticated:
        return jsonify(error="Authentication required"), 401
    if not current_user.is_admin:
        return jsonify(error="Administrator role required"), 403
    return jsonify({"access": "granted", "feature": "admin-report", "synthetic": True, "catalog": {"demo-games": 4, "demo-downloads": 128}})
