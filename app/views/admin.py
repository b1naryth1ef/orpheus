from flask import Blueprint, g, render_template, request

from helpers.user import UserGroup

from util.etc import paginate, get_or_cache_nickname
from util.errors import UserError, APIError
from util.responses import APIResponse

admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.before_request
def admin_before_request():
    print g.session._id
    if not g.user or not g.group:
        raise UserError("Yeah right...", "error")

    if g.group not in [UserGroup.ADMIN, UserGroup.SUPER]:
        raise UserError("Sorry, what?", "error")

@admin.route("/")
def admin_dashboard():
    return render_template("admin/index.html")

@admin.route("/users")
def admin_users():
    return render_template("admin/users.html")

USERS_LIST_QUERY = """
    SELECT id, steamid, email, date_part('epoch', last_login) as last_login FROM users ORDER BY id LIMIT %s OFFSET %s
"""

@admin.route("/api/user/list")
def admin_users_list():
    page = int(request.values.get("page", 1))

    g.cursor.execute("SELECT count(*) as c FROM users")
    pages = g.cursor.fetchone().c / 100

    g.cursor.execute(USERS_LIST_QUERY, paginate(page, per_page=100))
    users = []
    for entry in g.cursor.fetchall():
        users.append({
            "id": entry.id,
            "steamid": entry.steamid,
            "username": get_or_cache_nickname(entry.steamid),
            "last_login": entry.last_login
        })

    return APIResponse({"users": users, "pages": pages})
