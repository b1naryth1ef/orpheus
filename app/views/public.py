from flask import Blueprint, render_template, g
from markdown import Markdown

from util.perms import authed

public = Blueprint("public", __name__)

rules_content = Markdown().convert(open("docs/rules.md").read())

@public.route("/")
def route_index():
    return render_template("index.html")

@public.route("/match/<int:matchid>")
def route_bet_mid(matchid):
    return render_template("match.html")

@public.route("/rules")
def route_faq():
    return render_template("rules.html", content=rules_content)

@public.route("/profile/<id>")
@public.route("/profile")
def route_profile(id=None):
    return render_template("profile.html")

