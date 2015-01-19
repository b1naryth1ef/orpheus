from flask import Blueprint, g, render_template, request

from database import map_db_values

from helpers import get_count
from helpers.user import UserGroup
from helpers.game import create_game

from util.etc import paginate, get_or_cache_nickname
from util.errors import UserError, APIError
from util.responses import APIResponse

admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.before_request
def admin_before_request():
    print g.session._id
    if not g.user or not g.group:
        raise UserError("Yeah right...", "error")

    if g.group not in [UserGroup.ADMIN, UserGroup.SUPER]:
        raise UserError("Sorry, what?", "error")

@admin.route("/")
def admin_dashboard():
    return render_template("admin/index.html",
        users_count=get_count("users"),
        games_count=get_count("games"),
        matches_count=get_count("matches"),
        bets_count=get_count("bets"))

@admin.route("/users")
def admin_users():
    return render_template("admin/users.html")

@admin.route("/games")
def admin_games():
    return render_template("admin/games.html")

USERS_LIST_QUERY = """
    SELECT id, steamid, email, active, date_part('epoch', last_login) as last_login FROM users ORDER BY id LIMIT %s OFFSET %s
"""

@admin.route("/api/user/list")
def admin_users_list():
    page = int(request.values.get("page", 1))

    g.cursor.execute("SELECT count(*) as c FROM users")
    pages = (g.cursor.fetchone().c / 100) + 1

    g.cursor.execute(USERS_LIST_QUERY, paginate(page, per_page=100))

    users = []
    for entry in g.cursor.fetchall():
        users.append({
            "id": entry.id,
            "steamid": entry.steamid,
            "username": get_or_cache_nickname(entry.steamid),
            "last_login": entry.last_login,
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

    sql = "UPDATE users SET {} WHERE id=%(id)s".format(map_db_values(query))

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

    sql = "UPDATE games SET {} WHERE id=%(id)s".format(map_db_values(query))

    query['id'] = game
    g.cursor.execute(sql, query)

    return APIResponse()
