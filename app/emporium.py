import os, sys
from flask import Flask
from flask.ext.openid import OpenID

app = Flask(__name__)

app.config.from_pyfile("settings.py")

oid = OpenID(app)

def load_all_views():
    """
    Attempts to load all the subset blueprint views for the application
    """
    for view in os.listdir("views"):
        if not view.endswith(".py") or view.startswith("_"):
            continue

        view = "views." + view.split(".py")[0]
        __import__(view)
        app.register_blueprint(getattr(sys.modules[view], view.split(".")[-1]))

def load_event_handlers():
    from util import handlers

def setup():
    load_all_views()
    load_event_handlers()
