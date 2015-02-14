from flask import Blueprint, render_template, g
from markdown import Markdown

from util.perms import authed

public = Blueprint("public", __name__)

tos_content = Markdown().convert(open("docs/tos.md").read())
rules_content = Markdown().convert(open("docs/rules.md").read())
humans_content = open("static/humans.txt").read()

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

@public.route("/humans.txt")
def route_humans():
    return humans_content

@public.route("/rules")
def route_faq():
    return render_template("prose.html", content=rules_content)

@public.route("/tos")
def route_tos():
    return render_template("prose.html", content=tos_content)
