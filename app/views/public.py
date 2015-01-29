from flask import Blueprint, render_template, g

public = Blueprint("public", __name__)

@public.route("/")
def route_index():
    return render_template("index.html")

@public.route("/match/<int:matchid>")
def route_bet_mid(matchid):
    return render_template("match.html")
