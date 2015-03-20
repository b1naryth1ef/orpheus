import re, logging, psycopg2

from flask import Blueprint, g, redirect, flash
from datetime import datetime

from fort import oid, steam
from tasks.inventory import load_steam_inventory

from util import flashy
from util.errors import UserError, APIError
from util.responses import APIResponse

from helpers.user import create_user, gache_user_info, authed

auth = Blueprint("auth", __name__, url_prefix="/auth")
steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')
auto_admin_steamids = ["76561198037632722", "76561197960659425", "76561198142815401"]
log = logging.getLogger(__name__)

LOGIN_QUERY = """
SELECT u.id, u.active, u.ugroup, b.reason FROM users u
LEFT OUTER JOIN bans b ON (
    b.steamid=%(id)s AND b.start_date < now() AND b.end_date > now() AND b.active=true
)
WHERE u.steamid=%(id)s
"""

@oid.after_login
def create_or_login(resp):
    id = steam_id_re.findall(resp.identity_url)[0]

    user = g.cursor.execute(LOGIN_QUERY, {"id": id}).fetchone()

    if user:
        if user.reason:
            raise UserError("Banned:\n" + user.reason)

        if user.active:
            g.user = user.id
            g.group = user.ugroup
            g.cursor.execute("UPDATE users SET last_login=%s WHERE id=%s", (datetime.utcnow(), user.id))
        else:
            raise UserError("Account Disabled. Please contact support for more information")
        next_url = redirect(oid.get_next_url())
        flash("Welcome Back!", "success")
    else:
        allowed = steam.getGroupMembers("csgofort")
        if int(id) not in allowed:
            log.warning("User %s is not allowed in beta (%s)" % (id, allowed))
            raise UserError("Sorry, your not part of the beta! :(")

        if id in auto_admin_steamids:
            group = 'SUPER'
        else:
            group = 'NORMAL'
        g.user = create_user(id, group)
        g.group = group

        # Alright, lets try to onboard the user
        next_url = redirect("/?onboard=1")
        flash("Welcome to CSGO Fort!", "success")

    # Load the inventory to warm up the cache
    load_steam_inventory.queue(g.user)

    g.session["u"] = g.user
    return next_url

@auth.route("/login")
@oid.loginhandler
def route_login():
    if g.user:
        return redirect(oid.get_next_url())

    return oid.try_login("http://steamcommunity.com/openid")

@auth.route("/logout")
def route_logout():
    g.user = None
    return flashy("You have been logged out!")

@auth.route("/ping")
@authed()
def route_ping():
    return "pong"

@auth.route("/info")
def route_info():
    raise APIError("Deprecated")

