import os, sys, uuid
from slimit import minify

from flask import Flask, render_template
from flask.ext.openid import OpenID

from util.steam import SteamAPI, SteamMarketAPI

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

def get_js_source():
    for (curdir, dirs, files) in os.walk("js/"):
        for fname in files:
            if fname.endswith(".js"):
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
        f.write(minify(TEMPLATES, mangle=True))

# These must be loaded first
SOURCE_ORDER = {"js/app.js", "js/util.js"}

def build_js_source():
    SOURCE = ""

    SOURCE_ITER = list(SOURCE_ORDER) + list(set(get_js_source()) - SOURCE_ORDER)
    for source in SOURCE_ITER:
        with open(source) as f:
            SOURCE += f.read()

    with open("static/js/compiled.js", "w") as f:
        if app.config.get("ENV") == "PROD":
            f.write(minify(SOURCE, mangle=True))
        else:
            f.write(SOURCE)

def setup():
    load_all_views()
    load_event_handlers()
    build_js_templates()
    build_js_source()

