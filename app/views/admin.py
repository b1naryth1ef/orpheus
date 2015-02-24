import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Blueprint, g, render_template, request

from database import Cursor, redis

from helpers.user import UserGroup
from helpers.game import create_game
from helpers.match import create_match, match_to_json
from helpers.bot import get_bot_space

from util import paginate
from util.errors import UserError, APIError, EmporiumException
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
    rush_conn = redis.get("rush:open")
    bots_online = g.cursor.execute("SELECT count(*) as c FROM bots WHERE status='USED'").fetchone().c
    bot_used, bot_total = get_bot_space()
    b_cap = 100 - (((float(bot_used or 0) / bot_total)) * 100)
    return render_template("admin/index.html",
        users_count=g.cursor.count("users"),
        games_count=g.cursor.count("games"),
        matches_count=g.cursor.count("matches"),
        bets_count=g.cursor.count("bets"),
        b_used=bot_used,
        b_total=bot_total,
        b_cap=b_cap,
        rush_conn=rush_conn,
        bots_online=bots_online)

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
SELECT id, steamid, email, active, last_login, ugroup
FROM users {} ORDER BY id LIMIT %s OFFSET %s
"""

@admin.route("/api/user/list")
def admin_users_list():
    page = int(request.values.get("page", 1))

    q = ""
    if request.values.get("query"):
        # TODO: injection
        q = "WHERE steamid='%s'" % request.values.get("query")

    g.cursor.execute("SELECT count(*) as c FROM users {}".format(q))
    pages = (g.cursor.fetchone().c / 50) + 1

    g.cursor.execute(USERS_LIST_QUERY.format(q), paginate(page, per_page=50))

    users = []
    for entry in g.cursor.fetchall():
        users.append({
            "id": entry.id,
            "steamid": entry.steamid,
            "username": None,
            "last_login": entry.last_login.strftime("%s") if entry.last_login else 0,
            "ugroup": entry.ugroup,
            "active": entry.active
        })

    return APIResponse({"users": users, "pages": pages})

USER_EDITABLE_FIELDS = [
    "email", "active", "ugroup"
]

@admin.route("/api/user/edit", methods=["POST"])
def admin_user_edit():
    user = request.values.get("user")

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

    games = {}
    for entry in g.cursor.fetchall():
        games[entry.id] = {
            "id": entry.id,
            "name": entry.name,
            "appid": entry.appid,
            "active": entry.active
        }

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
SELECT * FROM matches ORDER BY id LIMIT %s OFFSET %s;
"""

@admin.route("/api/match/list")
def admin_match_list():
    page = int(request.values.get("page", 1))

    g.cursor.execute("SELECT count(*) as c FROM matches")
    pages = (g.cursor.fetchone().c / 100) + 1

    g.cursor.execute(MATCHES_LIST_QUERY, paginate(page, per_page=100))

    matches = {}
    for entry in g.cursor.fetchall():
        matches[entry.id] = match_to_json(entry)

    return APIResponse({"matches": matches, "pages": pages})

MATCH_FIELDS = {
    "game", "event", "maplist", "match_date", "public_date",
    "team1", "team2"
}

def parse_match_payload(obj):
    diff = MATCH_FIELDS - set(obj.keys())
    if len(diff) != 0:
        raise APIError("Missing fields: %s" % ', '.join(diff))

    if not obj['match_date']:
        raise APIError("Need a match date")

    match_date = datetime.fromtimestamp(int(obj['match_date']))

    if obj['public_date']:
        public_date = datetime.fromtimestamp(int(obj['public_date']))
    else:
        public_date = match_date - relativedelta(days=2)

    maps = map(lambda i: i.strip(), obj['maplist'].split(",")) if obj['maplist'] else None

    with Cursor() as c:
        game_ok = c.execute("SELECT id FROM games WHERE id=%s", (request.json['game'], )).fetchone()
        if not game_ok:
            raise APIError("Invalid Game ID")

        event_ok = c.execute("SELECT id, games FROM events WHERE id=%s", (request.json['event'], )).fetchone()
        if not event_ok:
            raise APIError("Invalid Event ID")

        # Make sure the event is involved with the game
        if not int(game_ok.id) in event_ok.games:
            raise APIError("That game is not part of that event!")

        teams_ok = c.execute("SELECT id FROM teams WHERE id in %s",
            ((request.json['team1'], request.json['team2']),)).fetchall()
        if not len(teams_ok) == 2 and len(set(map(lambda i: i.id, teams_ok))) == len(teams_ok):
            raise APIError("Invalid Team ID's")

        return match_date, public_date, maps, game_ok.id, event_ok.id, map(lambda i: i.id, teams_ok), obj.get("active", False)

@admin.route("/api/match/create", methods=["POST"])
def admin_match_create():
    match_date, public_date, maps, game, event, teams, active = parse_match_payload(request.json)

    with Cursor() as c:
        c.insert("matches", {
            "state": "OPEN",
            "itemstate": "OPEN",
            "event": event,
            "game": game,
            "teams": teams,
            "meta": c.json({
                "maps": maps
            }),
            "max_value_item": 60,
            "lock_date": match_date - relativedelta(minutes=5),
            "match_date": match_date,
            "public_date": public_date,
            "active": active,
            "created_by": g.user,
            "created_at": datetime.utcnow()
        })

    return APIResponse()

@admin.route("/api/match/<id>/edit", methods=["POST"])
def admin_match_edit(id):
    match_date, public_date, maps, game, event, teams, active = parse_match_payload(request.json)

    data = {
        "id": id,
        "event": event,
        "game": game,
        "teams": teams,
        "active": active,
        "match_date": match_date,
        "public_date": public_date
    }
    print data

    with Cursor() as c:
        pre, post = c.paramify(data)
        c.execute("""
            UPDATE matches SET
                event=%(event)s, game=%(game)s, teams=%(teams)s, active=%(active)s, match_date=%(match_date)s,
                public_date=%(public_date)s
            WHERE id=%(id)s""", data)

    return APIResponse()


DRAFT_MATCHES_QUERY = """
    SELECT id, teams, state, itemstate FROM matches WHERE id=%s
"""
DRAFT_KEYS = ['state', 'winner', 'meta']
DRAFT_STATES = ['state-completed', 'state-closed', 'state-locked']

@admin.route("/api/match/results", methods=["POST"])
def admin_match_results():
    match = g.cursor.execute(DRAFT_MATCHES_QUERY, (request.json['id'], )).fetchone()

    # We couldn't find a match for that id
    if not match:
        raise APIError("Invalid Match")

    # Items must be locked to enter results
    if match.itemstate != 'LOCKED':
        raise APIError("Cannot enter result for match which is not item-locked")

    if request.json['state'] not in DRAFT_STATES:
        raise APIError("Invalid Draft State")

    match_state = None
    match_results = {}

    if request.json['state'] == 'state-completed':
        if not request.json['winner']:
            raise APIError("Cannot mark match as completed without a winner!")

        winner = request.json['winner']
        if int(winner) not in match.teams:
            raise APIError("Invalid match winner")

        match_state = "RESULT"
        match_results['winner'] = int(winner)
        match_results['meta'] = request.json['meta']
    elif request.json['state'] == 'state-closed':
        match_state = "CLOSED"
    elif request.json['state'] == 'state-locked':
        match_state = "LOCKED"

    g.cursor.execute("""
        UPDATE matches SET state=%s, results=%s WHERE id=%s
    """, (match_state, g.cursor.json(match_results), match.id))

    return APIResponse()

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

TEAM_LIST_QUERY = """
SELECT * FROM teams ORDER BY id LIMIT %s OFFSET %s;
"""

@admin.route("/api/team/list")
def admin_team_list():
    page = int(request.values.get("page", 1))

    g.cursor.execute("SELECT count(*) as c FROM teams")
    pages = (g.cursor.fetchone().c / 100) + 1

    g.cursor.execute(TEAM_LIST_QUERY, paginate(page, per_page=100))

    teams = {}
    for entry in g.cursor.fetchall():
        teams[entry.id] = {
            "id": entry.id,
            "tag": entry.tag,
            "name": entry.name,
            "logo": entry.logo,
            "meta": entry.meta,
        }

    return APIResponse({"teams": teams, "pages": pages})

EVENT_LIST_QUERY = """
SELECT * FROM events {} ORDER BY id LIMIT %s OFFSET %s;
"""

@admin.route("/api/event/list")
def admin_event_list():
    page = int(request.values.get("page", 1))

    q = ""
    if request.values.get("active"):
        q = "WHERE active=true AND start_date < now() AND (end_date > now() OR end_date IS NULL)"

    g.cursor.execute("SELECT count(*) as c FROM events {}".format(q))
    pages = (g.cursor.fetchone().c / 100) + 1

    g.cursor.execute(EVENT_LIST_QUERY.format(q), paginate(page, per_page=100))

    events = {}
    for entry in g.cursor.fetchall():
        events[entry.id] = {
            "id": entry.id,
            "name": entry.name,
            "type": entry.etype,
            "website": entry.website,
            "league": entry.league,
            "logo": entry.logo,
            "splash": entry.splash,
            "streams": entry.streams,
            "games": entry.games,
        }

    return APIResponse({"events": events, "pages": pages})

