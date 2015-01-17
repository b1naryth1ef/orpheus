import re

from flask import Blueprint, g, redirect
from datetime import datetime

from util import flashy
from util.etc import get_or_cache_nickname
from util.errors import UserError, APIError
from util.responses import APIResponse

from emporium import oid
from helpers.user import create_user

auth = Blueprint("auth", __name__, url_prefix="/auth")
steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')
auto_admin_steamids = ["76561198037632722"]

@oid.after_login
def create_or_login(resp):
    id = steam_id_re.findall(resp.identity_url)[0]

    g.cursor.execute("SELECT id, active, ugroup FROM users WHERE steamid=%s", (id, ))
    user = g.cursor.fetchone()

    if user:
        if user.active:
            g.user = user.id
            g.group = user.ugroup
            g.cursor.execute("UPDATE users SET last_login=%s WHERE id=%s", (datetime.utcnow(), user.id))
        else:
            raise UserError("Account Disabled. Please contact support for more information")
    else:
        if id in auto_admin_steamids:
            group = 'super'
        else:
            group = 'normal'
        g.user = create_user(id, group)
        g.group = group

    g.session["u"] = g.user
    return redirect(oid.get_next_url())

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

@auth.route("/info")
def route_info():
    if not g.user:
        return APIResponse({
            "authed": False
        })

    g.cursor.execute("SELECT steamid, settings, ugroup FROM users WHERE id=%s", (g.user, ))
    resp = g.cursor.fetchone()

    if not resp:
        g.user = None
        return APIResponse({
            "authed": False
        })

    return APIResponse({
        "authed": True,
        "user": {
            "id": g.user,
            "name": get_or_cache_nickname(resp.steamid),
            "steamid": str(resp.steamid),
            "settings": resp.settings,
            "group": resp.ugroup
        }
    })

