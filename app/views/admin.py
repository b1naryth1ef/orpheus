from flask import Blueprint, g, render_template

from helpers.user import UserGroup

from util.errors import UserError, APIError
from util.responses import APIResponse

admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.before_request
def admin_before_request():
    if not g.user or not g.group:
        raise UserError("Yeah right...", "error")

    if g.group not in [UserGroup.ADMIN, UserGroup.SUPER]:
        raise UserError("Sorry, what?", "error")

@admin.route("/")
def admin_dashboard():
    return render_template("admin/index.html")

