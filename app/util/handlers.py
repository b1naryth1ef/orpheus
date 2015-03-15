import json, logging, traceback, sys, psycopg2

from flask import request, g, redirect, render_template, get_flashed_messages

from fort import app
from database import Cursor

from helpers.common import create_exception
from helpers.user import get_user_info

from util.sessions import Session
from util.errors import ResponseException, GenericError
from util.responses import APIResponse
from util.slack import SlackMessage

log = logging.getLogger(__name__)

@app.errorhandler(500)
def internal_error_handler(exception):
    trace_id = None

    try:
        trace_id = create_exception(exception, {
            "uid": g.user,
            "sid": g.session._id,
            "ip": request.remote_addr,
            "url": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "values": dict(request.values)
        })
    except psycopg2.Error:
        log.exception("Failed to save exception trace: ")

    try:
        exc_type, exc_obj, exc_tb = sys.exc_info()

        content = ''.join(traceback.format_exception(exc_type, exc_obj, exc_tb))
        msg = SlackMessage("Web Exception (%s)" % str(exc_obj), color='danger')
        msg.add_custom_field("Request", "%s %s" % (request.method, request.path))
        msg.add_custom_field("IP", request.remote_addr)
        msg.add_custom_field("User ID", g.user)
        msg.add_custom_field("Session ID", g.session._id)
        msg.add_custom_field("Trace", str(trace_id))
        msg.add_custom_field("Exception", content)
        msg.send_async()
    except Exception:
        log.exception("Failed to send slack exception trace: ")

    app.logger.exception("Server Exception (%s)" % trace_id)
    return render_template("error.html", code=500, msg="Internal Server Exception", trace=trace_id), 500

@app.errorhandler(404)
def page_not_found_handler(exception):
    return render_template("error.html", code=404, msg="Page Not Found!"), 404

@app.context_processor
def app_context_processor():
    base = {
        "notifications": get_flashed_messages(with_categories=True)
    }

    if 'user' in g:
        base.update(get_user_info(g.user))
    return {"user": base}

@app.template_filter("jsonify")
def jsonify_filter(x):
    return json.dumps(x)

@app.before_request
def app_before_request():
    if '/static/' in request.path:
        return

    # Load session if it exists
    g.session = Session()
    if g.session.new():
        g.session["ip"] = request.remote_addr
    elif g.session["ip"] != request.remote_addr:
        g.session.end()
        return redirect("/")

    g.user = None
    g.group = "normal"

    # Set a user for testing
    if app.config.get("TESTING"):
        if 'FAKE_USER' in request.headers:
            log.debug("TESTING: Faking user %s", request.headers.get("FAKE_USER"))
            g.user = int(request.headers.get("FAKE_USER"))
            g.group = "normal"
        if 'FAKE_GROUP' in request.headers:
            log.debug("TESTING: Faking group %s", request.headers.get("FAKE_GROUP"))
            g.group = request.headers.get("FAKE_GROUP")
    else:
        # Set uid
        g.user = g.session.get("u")
        g.group = g.session.get("g")

    # Setup DB transaction
    g.cursor = Cursor()

@app.after_request
def app_after_request(response):
    if '/static/' in request.path:
        return response

    # Update the session if applicable
    if g.user:
        g.session["g"] = g.group
        g.session["u"] = g.user

        # Save session if it changed
        g.session.save(response)
    else:
        g.session.end()

    g.cursor.close()
    return response

@app.errorhandler(ResponseException)
def app_response_error(err):
    return err.to_response()

