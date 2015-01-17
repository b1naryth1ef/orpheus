from flask import request, g
from psycopg2 import OperationalError

from emporium import app
from database import db
from util.sessions import Session
from util.errors import ResponseException, GenericError
from util.responses import APIResponse

@app.before_request
def app_before_request():
    if '/static/' in request.path:
        return

    # Load session if it exists
    g.session = Session()

    g.user = None
    g.group = None

    # Set a user for testing
    if app.config.get("TESTING"):
        if 'FAKE_USER' in request.headers:
            g.user = int(request.headers.get("FAKE_USER"))
            g.group = "normal"
        if 'FAKE_GROUP' in request.headers:
            g.group = request.headers.get("FAKE_GROUP")
    else:
        # Set uid
        g.user = g.session.get("u")
        g.group = g.session.get("g")

    # Setup DB transaction
    try:
        g.db = db.getconn()
        g.cursor = g.db.cursor()
    except OperationalError:
        g.db = None
        raise GenericError("The site is currently experiencing issues.", code=500)

@app.after_request
def app_after_request(response):
    if '/static/' in request.path:
        return response

    # Set userid
    if g.user:
        g.session["g"] = g.group
        g.session["u"] = g.user
    else:
        g.session.delete("g")
        g.session.delete("u")

    # Save session if it changed
    g.session.save(response)

    # Commit DB changes for request
    if g.db:
        if not g.db.closed:
            g.db.commit()
        db.putconn(g.db)

    return response

@app.errorhandler(ResponseException)
def app_response_error(err):
    return err.to_response()
