from flask import g

from emporium import app
from database import db
from util.sessions import Session

@app.before_request
def app_before_request():
    # Load session if it exists
    g.session = Session()

    # Set uid
    g.user = g.session.get("uid")

    # Setup DB transaction
    g.db = db.getconn()
    g.cursor = g.db.cursor()

@app.after_request
def app_after_request(response):
    # Set userid
    if g.user:
        g.session["uid"] = g.user

    # Save session if it changed
    g.session.save(response)

    # Commit DB changes for request
    g.db.commit()
    db.putconn(g.db)

    return response

