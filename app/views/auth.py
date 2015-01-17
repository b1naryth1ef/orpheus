import re

from flask import Blueprint, g, redirect

from emporium import oid
from helpers.user import create_user

auth = Blueprint("auth", __name__, url_prefix="/auth")
steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')

@oid.after_login
def create_or_login(resp):
    id = steam_id_re.findall(resp.identity_url)[0]

    g.cursor.execute("SELECT id, active FROM users WHERE steamid=%s", (id, ))
    results = g.cursor.fetchall()

    if len(results):
        if results[0].active:
            g.user = results[0].id
        else:
            # TODO: throw error to user, they are not allowed to login
            return None
    else:
        g.user = create_user(id)

    g.session["uid"] = g.user
    return redirect(oid.get_next_url())

@auth.route("/login")
@oid.loginhandler
def route_login():
    if g.user:
        return redirect(oid.get_next_url())

    return oid.try_login("http://steamcommunity.com/openid")

@auth.route("/logout")
def route_logout():
    del g.session["uid"]


