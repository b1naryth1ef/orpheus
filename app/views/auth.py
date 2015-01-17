import re

from flask import Blueprint, g

from emporium import oid
from helpers.user import create_user

auth = Blueprint("auth", __name__, url_prefix="/auth")
steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')

@oid.after_login
def create_or_login(resp):
    id = steam_id_re.findall(resp.identity_url)[0]

    g.cursor.execute("SELECT (id, active) FROM users WHERE steamid=%s", id)
    results = g.cursor.findall()

    if len(results):
        if results[0].active:
            g.user = results[0].id
        else:
            # TODO: throw error to user, they are not allowed to login
            return None
    else:
        g.user = create_user(id)

    return redirect(oid.get_next_url())

@auth.route("/login")
def route_login():
    pass

@auth.route("/logout")
def route_logout():
    pass


