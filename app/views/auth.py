from flask import Blueprint

auth = Blueprint("auth", __name__, url_prefix="/auth")

@auth.route("/login")
def route_login():
    pass

@auth.route("/logout")
def route_logout():
    pass
