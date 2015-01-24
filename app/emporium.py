import os, sys

from flask import Flask
from flask.ext.openid import OpenID

from util.steam import SteamAPI

app = Flask(__name__)

app.config.from_pyfile("settings.py")

oid = OpenID(app)

steam = SteamAPI(app.config.get("STEAM_API_KEY"))

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

def get_js_templates():
    for (curdir, dirs, files) in os.walk("templates/"):
        for fname in files:
            if "/js" in curdir and fname.endswith(".html"):
                yield os.path.join(curdir, fname)

def build_js_templates():
    TEMPLATES = "var T = {};"

    for jst in get_js_templates():
        p = open(jst)
        TEMPLATES += 'T.%s = _.template("%s");\n' % (
            jst.rsplit("/", 1)[-1].rsplit(".", 1)[0],
            p.read().replace("\n", "").replace('"', "\\\"")
        )
        p.close()

    with open("static/js/templates.js", "w") as f:
        f.write(TEMPLATES)

def setup():
    load_all_views()
    load_event_handlers()
    build_js_templates()

