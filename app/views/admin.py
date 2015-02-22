import base64
from flask import Blueprint, g, render_template, request

from database import Cursor

from helpers.user import UserGroup
from helpers.game import create_game
from helpers.match import create_match
from helpers.bot import get_bot_space

from util import paginate
from util.errors import UserError, APIError
from util.responses import APIResponse

admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.before_request
def admin_before_request():
    if not g.user or not g.group:
        raise UserError("Yeah right...", "error")

    if g.group not in [UserGroup.ADMIN, UserGroup.SUPER]:
        raise UserError("Sorry, what?", "error")

@admin.route("/")
def admin_dashboard():
    bot_used, bot_total = get_bot_space()
    b_cap = 100 - (((float(bot_used or 0) / bot_total)) * 100)
    return render_template("admin/index.html",
        users_count=g.cursor.count("users"),
        games_count=g.cursor.count("games"),
        matches_count=g.cursor.count("matches"),
        bets_count=g.cursor.count("bets"),
        b_used=bot_used,
        b_total=bot_total,
        b_cap=b_cap)

@admin.route("/users")
def admin_users():
    return render_template("admin/users.html")

@admin.route("/games")
def admin_games():
    return render_template("admin/games.html")

@admin.route("/matches")
def admin_matches():
    return render_template("admin/matches.html")

USERS_LIST_QUERY = """
SELECT id, steamid, email, active, last_login
FROM users WHERE id > %s ORDER BY id LIMIT %s
"""

@admin.route("/api/user/list")
def admin_users_list():
    page = int(request.values.get("page", 1))

    g.cursor.execute("SELECT count(*) as c FROM users")
    pages = (g.cursor.fetchone().c / 50) + 1

    a, b = paginate(page, per_page=50)
    g.cursor.execute(USERS_LIST_QUERY, (b, a))

    users = []
    for entry in g.cursor.fetchall():
        users.append({
            "id": entry.id,
            "steamid": entry.steamid,
            "username": None,
            "last_login": entry.last_login.strftime("%s") if entry.last_login else 0,
            "active": entry.active
        })

    return APIResponse({"users": users, "pages": pages})

USER_EDITABLE_FIELDS = [
    "email", "active"
]

@admin.route("/api/user/edit", methods=["POST"])
def admin_user_edit():
    user = request.values.get("user")
    print user

    g.cursor.execute("SELECT id FROM users WHERE id=%s", (user, ))
    if not g.cursor.fetchone():
        raise APIError("Invalid User")

    query = {k: v for (k, v) in request.values.iteritems() if k in USER_EDITABLE_FIELDS}
    if not len(query):
        raise APIError("Nothing to change!")

    sql = "UPDATE users SET {} WHERE id=%(id)s".format(Cursor.map_values(query))

    query['id'] = user
    g.cursor.execute(sql, query)

    return APIResponse()

GAMES_LIST_QUERY = """
SELECT id, name, appid, active FROM games ORDER BY id LIMIT %s OFFSET %s
"""

@admin.route("/api/game/list")
def admin_game_list():
    page = int(request.values.get("page", 1))

    g.cursor.execute("SELECT count(*) as c FROM games")
    pages = (g.cursor.fetchone().c / 100) + 1

    g.cursor.execute(GAMES_LIST_QUERY, paginate(page, per_page=100))

    games = []
    for entry in g.cursor.fetchall():
        games.append({
            "id": entry.id,
            "name": entry.name,
            "appid": entry.appid,
            "active": entry.active
        })

    return APIResponse({"games": games, "pages": pages})

@admin.route("/api/game/create", methods=["POST"])
def admin_game_create():
    try:
        id = create_game(g.user, request.values["name"], int(request.values["appid"]))
    except Exception, e:
        raise APIError("Invalid Data: %s" % e)

    return APIResponse({
        "game": id
    })

GAME_EDITABLE_FIELDS = [
    "name", "appid", "active"
]

@admin.route("/api/game/edit", methods=["POST"])
def admin_edit_game():
    game = request.values.get("game")

    g.cursor.execute("SELECT id FROM games WHERE id=%s", (game, ))
    if not g.cursor.fetchone():
        raise APIError("Invalid Game")

    query = {k: v for (k, v) in request.values.iteritems() if k in GAME_EDITABLE_FIELDS}
    if not len(query):
        raise APIError("Nothing to change!")

    sql = "UPDATE games SET {} WHERE id=%(id)s".format(Cursor.map_values(query))

    query['id'] = game
    g.cursor.execute(sql, query)

    return APIResponse()

MATCHES_LIST_QUERY = """
SELECT id, game, teams, meta, results, active, lock_date, match_date, public_date
FROM matches ORDER BY id LIMIT %s OFFSET %s;
"""

@admin.route("/api/match/list")
def admin_match_list():
    page = int(request.values.get("page", 1))

    g.cursor.execute("SELECT count(*) as c FROM matches")
    pages = (g.cursor.fetchone().c / 100) + 1

    g.cursor.execute(MATCHES_LIST_QUERY, paginate(page, per_page=100))

    matches = []
    for entry in g.cursor.fetchall():
        matches.append({
            "id": entry.id,
            "game": entry.game,
            "teams": entry.teams,
            "meta": entry.meta,
            "results": entry.results,
            "active": entry.active,
            "lock_date": entry.lock_date.strftime("%s"),
            "match_date": entry.match_date.strftime("%s"),
            "public_date": entry.public_date.strftime("%s")
        })

    return APIResponse({"matches": matches, "pages": pages})

@admin.route("/api/match/create", methods=["POST"])
def admin_match_create():
    pass

@admin.route("/api/bots/export")
def admin_bots_export():
    # lol yeah...
    assert(g.user == 1)

    bots = g.cursor.execute("""
        SELECT steamid, username, password, sentry FROM bots
    """).fetchall()

    res = []
    for bot in bots:
        res.append({
            "steamid": bot.steamid,
            "username": bot.username,
            "password": bot.password,
            "sentry": base64.b64encode(bot.sentry)
        })

    return APIResponse({"bots": res})

