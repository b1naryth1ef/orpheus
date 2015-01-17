from flask import Blueprint, render_template, g

public = Blueprint("public", __name__)

@public.route("/")
def route_index():
    return render_template("index.html")

@public.route("/about")
def route_about():
    return render_template("about.html")

@public.route("/bet")
def route_bet():
    return render_template("bet.html")

