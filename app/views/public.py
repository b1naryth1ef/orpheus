from flask import Blueprint, render_template, g

from util.perms import authed

public = Blueprint("public", __name__)

@public.route("/")
def route_index():
    return render_template("index.html")

@public.route("/match/<int:matchid>")
def route_bet_mid(matchid):
    return render_template("match.html")

@public.route("/profile/<id>")
@public.route("/profile")
def route_profile(id=None):
    return render_template("profile.html")

