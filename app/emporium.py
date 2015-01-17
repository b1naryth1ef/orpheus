import os, sys

from flask import Flask
from flask.ext.openid import OpenID

from util.log import setup_logging

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

def build_js_templates():
    TEMPLATES = "var T = {};"

    for (curdir, dirs, files) in os.walk("templates/"):
        for fname in files:
            if "/js" in curdir and fname.endswith(".html"):
                p = open(os.path.join(curdir, fname))
                TEMPLATES += 'T["%s"] = _.template("%s");' % (
                    fname.rsplit(".", 1)[0],
                    p.read().replace("\n", "").replace('"', "'")
                )
                p.close()

    with open("static/js/templates.js", "w") as f:
        f.write(TEMPLATES)

def setup():
    setup_logging()
    load_all_views()
    load_event_handlers()
    build_js_templates()
