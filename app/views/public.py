from flask import Blueprint, render_template, g, send_from_directory
from markdown import Markdown

from fort import app
from helpers.user import authed

public = Blueprint("public", __name__)

rules_content = Markdown().convert(open("docs/rules.md").read())
humans_content = open("static/humans.txt").read()

@public.route("/")
def route_index():
    return render_template("index.html")
    
@public.route("/events")
@public.route("/event/<int:eventid>")
def route_events_page(eventid=None):
    return render_template("events.html")

@public.route("/match/<int:matchid>")
def route_bet_mid(matchid):
    return render_template("match.html")

@public.route("/profile/<id>")
@public.route("/profile")
def route_profile(id=None):
    return render_template("profile.html")

@public.route("/settings")
@authed()
def route_settings():
    return render_template("settings.html")

@public.route("/news")
def route_news_page():
    return render_template("news.html")

@public.route("/humans.txt")
def route_humans():
    return humans_content

@public.route("/rules")
def route_faq():
    return render_template("prose.html", content=rules_content)

if app.config.get("ENV") != "PROD":
    @public.route("/img/<name>")
    def serve_image(name):
        return send_from_directory("static/img/usr/", name)

