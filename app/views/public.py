from flask import Blueprint, render_template, g

public = Blueprint("public", __name__)

@public.route("/")
def route_index():
    g.cursor.execute("SELECT id, username FROM accounts")
    results = g.cursor.fetchall()
    print map(lambda i: i.username, results)
    return render_template("home.html")

@public.route("/about")
def route_about():
    return render_template("about.html")

@public.route("/bet")
def route_bet():
    return render_template("bet.html")

