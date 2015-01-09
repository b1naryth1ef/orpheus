from flask import g
from emporium import app
from database import db

@app.before_request
def app_before_request():
    g.db = db.getconn()
    g.cursor = g.db.cursor()

@app.after_request
def app_after_request():
    g.db.commit()
    db.putconn(g.db)

