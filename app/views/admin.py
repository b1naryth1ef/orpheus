import base64, uuid, os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Blueprint, g, render_template, request
from fort import app

from database import Cursor, redis

from helpers.user import UserGroup, authed
from helpers.game import create_game
from helpers.match import create_match, match_to_json
from helpers.bot import get_bot_space
from helpers.common import get_enum_array
from helpers.news import create_news_post, update_news_post

from util import paginate, from_js_datetime
from util.errors import UserError, APIError, FortException
from util.responses import APIResponse
from util.sessions import find_sessions_for_user

admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.before_request
def admin_before_request():
    if not g.user or not g.group:
        raise UserError("Yeah right...", "danger")

    if g.group not in [UserGroup.MODERATOR, UserGroup.ADMIN, UserGroup.SUPER]:
        raise UserError("Sorry, what?", "danger")

@admin.route("/")
def admin_dashboard():
    rush_conn = redis.get("rush:open")
    bots_online = g.cursor.execute("SELECT count(*) as c FROM bots WHERE status='USED'").fetchone().c
    bot_used, bot_total = get_bot_space()
    b_cap = (100 - (((float(bot_used or 0) / bot_total)) * 100)) or 0

    return render_template("admin/index.html",
        users_count=g.cursor.count("users"),
        games_count=g.cursor.count("games"),
        matches_count=g.cursor.count("matches"),
        events_count=g.cursor.count("events"),
        teams_count=g.cursor.count("teams"),
        bets_count=g.cursor.count("bets"),
        newsposts_count=g.cursor.count("newsposts"),
        bans_count=g.cursor.count("bans"),
        b_used=bot_used,
        b_total=bot_total,
        b_cap=b_cap,
        rush_conn=rush_conn,
        bots_online=bots_online)

@admin.route("/bans")
@authed(UserGroup.ADMIN)
def admin_bans():
    return render_template("admin/bans.html")

@admin.route("/users")
@authed(UserGroup.ADMIN)
def admin_users():
    return render_template("admin/users.html")

@admin.route("/games")
@authed(UserGroup.ADMIN)
def admin_games():
    return render_template("admin/games.html")

@admin.route("/matches")
def admin_matches():
    return render_template("admin/matches.html")

@admin.route("/teams")
def admin_teams():
    return render_template("admin/teams.html")

@admin.route("/events")
def admin_events():
    return render_template("admin/events.html")

@admin.route("/news")
def admin_news():
    return render_template("admin/news.html")

IMAGE_PATH = "/var/data/img" if app.config.get("ENV") == "PROD" else "static/img/usr"
EXTS = {"png", "jpg", "gif"}

@admin.route("/api/image/upload", methods=['POST'])
def admin_upload_image():
    results = {}
    for k, f in request.files.items():

        if '.' not in f.filename or f.filename.rsplit(".", 1)[1] not in EXTS:
            raise APIError("Invalid File Format")

        name = str(uuid.uuid4()) + '.' + f.filename.rsplit(".", 1)[1]
        f.save(os.path.join(IMAGE_PATH, name))
        results[k] = name

    return APIResponse({
        "images": results,
    })


USERS_LIST_QUERY = """
SELECT id, steamid, email, active, last_login, ugroup
FROM users {} ORDER BY id LIMIT %s OFFSET %s
"""

@admin.route("/api/user/list")
@authed(UserGroup.ADMIN, api=True)
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
            "last_login": entry.last_login.isoformat() if entry.last_login else "",
            "ugroup": entry.ugroup,
            "active": entry.active
        })

    return APIResponse({"users": users, "pages": pages})

USER_EDITABLE_FIELDS = [
    "email", "active", "ugroup"
]

@admin.route("/api/user/edit", methods=["POST"])
@authed(UserGroup.ADMIN, api=True)
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
@authed(UserGroup.ADMIN, api=True)
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
@authed(UserGroup.ADMIN, api=True)
def admin_game_create():
    id = create_game(g.user, request.values["name"], int(request.values["appid"]))

    return APIResponse({
        "game": id
    })

GAME_EDITABLE_FIELDS = [
    "name", "appid", "active"
]

@admin.route("/api/game/edit", methods=["POST"])
@authed(UserGroup.ADMIN, api=True)
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

    match_date = from_js_datetime(obj['match_date'])

    if obj['public_date']:
        public_date = from_js_datetime(obj['public_date'])
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

        # TODO: when we make this avail (Make sure the event is involved with the game)
        #if not int(game_ok.id) in event_ok.games:
        #    raise APIError("That game is not part of that event!")

        teams_ok = c.execute("SELECT id FROM teams WHERE id in %s",
            ((request.json['team1'], request.json['team2']),)).fetchall()
        if not len(teams_ok) == 2 and len(set(map(lambda i: i.id, teams_ok))) == len(teams_ok):
            raise APIError("Invalid Team ID's")

        bet_state = request.json.get("bet_state")
        bet_itemstate = request.json.get("bet_itemstate")

        return match_date, public_date, maps, game_ok.id, event_ok.id, map(lambda i: i.id, teams_ok), obj.get("active", False), bet_state, bet_itemstate

@admin.route("/api/match/create", methods=["POST"])
def admin_match_create():
    match_date, public_date, maps, game, event, teams, active, _, _ = parse_match_payload(request.json)
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
            "match_date": match_date,
            "public_date": public_date,
            "active": active,
            "created_by": g.user,
            "created_at": datetime.utcnow()
        })

    return APIResponse()

@admin.route("/api/match/<id>/edit", methods=["POST"])
def admin_match_edit(id):
    match_date, public_date, maps, game, event, teams, active, bet_state, bet_itemstate = parse_match_payload(request.json)

    data = {
        "id": id,
        "event": event,
        "game": game,
        "teams": teams,
        "active": active,
        "match_date": match_date,
        "public_date": public_date,
        "bet_state": bet_state,
        "bet_itemstate": bet_itemstate
    }

    with Cursor() as c:
        pre, post = c.paramify(data)
        c.execute("""
            UPDATE matches SET
                event=%(event)s, game=%(game)s, teams=%(teams)s, active=%(active)s, match_date=%(match_date)s, state=%(bet_state)s, itemstate=%(bet_itemstate)s,
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
        match_results['final'] = request.json['results']['final']
    elif request.json['state'] == 'state-closed':
        match_state = "CLOSED"
    elif request.json['state'] == 'state-locked':
        match_state = "LOCKED"

    g.cursor.execute("""
        UPDATE matches SET state=%s, results=%s WHERE id=%s
    """, (match_state, g.cursor.json(match_results), match.id))

    return APIResponse()

@admin.route("/api/bots/export")
@authed(UserGroup.SUPER, api=True)
def admin_bots_export():
    # lol yeah...

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

TEAM_LIST_QUERY = "SELECT * FROM teams ORDER BY id LIMIT %s OFFSET %s"

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

# TODO: Move all of the team stuff into it's own helper file.
TEAM_FIELDS = {
    "tag", "name", "logo"
}

def parse_team_payload(payload):
    empty_fields = [i for i in TEAM_FIELDS if not payload.get(i)]

    if len(empty_fields):
        raise APIError("Missing Fields: %s" % ' '.join(empty_fields))

    return payload['tag'], payload['name'], payload['logo']

@admin.route("/api/teams/create", methods=["POST"])
def admin_team_create():
    tag, name, logo = parse_team_payload(request.json)

    with Cursor() as c:
        c.insert("teams", {
            "tag": tag,
            "name": name,
            "logo": logo,
            "created_by": g.user,
            "created_at": datetime.utcnow()
        })

    return APIResponse()

@admin.route("/api/teams/<id>/edit", methods=["POST"])
def admin_team_edit(id):
    tag, name, logo = parse_team_payload(request.json)

    data = {
        "id": id,
        "tag": tag,
        "name": name,
        "logo": logo
    }

    with Cursor() as c:
        c.execute("""
            UPDATE teams
            SET tag=%(tag)s, name=%(name)s, logo=%(logo)s
            WHERE id=%(id)s"""
            , data)

    return APIResponse()

EVENT_FIELDS = { "name", "website", "league", "logo", "splash", "etype", "start_date", "end_date" , "active"}
EVENT_LIST_QUERY = "SELECT * FROM events {} ORDER BY id LIMIT %s OFFSET %s;"

@admin.route("/api/event/list")
def admin_event_list():
    page = int(request.values.get("page", 1))

    q = ""

    if request.values.get("active"):
        q = "WHERE start_date < now() AND (end_date > now() OR end_date IS NULL)"

    g.cursor.execute("SELECT count(*) as c FROM events {}".format(q))

    pages = (g.cursor.fetchone().c / 100) + 1

    g.cursor.execute(EVENT_LIST_QUERY.format(q), paginate(page, per_page=100))

    events = {}

    for entry in g.cursor.fetchall():
        events[entry.id] = {
            "id": entry.id,
            "name": entry.name,
            "etype": entry.etype,
            "website": entry.website,
            "league": entry.league,
            "logo": entry.logo,
            "splash": entry.splash,
            "streams": entry.streams,
            "games": entry.games,
            "start_date": entry.start_date.isoformat() if entry.start_date else "",
            "end_date": entry.end_date.isoformat() if entry.end_date else "",
            "active": entry.active,
        }

    eventtypes = get_enum_array("EVENT_TYPE")

    return APIResponse({"events": events, "eventtypes": eventtypes, "pages": pages})

@admin.route("/api/events/create", methods=["POST"])
def admin_event_create():
    missing = EVENT_FIELDS - set(request.json.keys())
    if len(missing):
        raise APIError("Missing Fields: %s" % ', '.join(missing))

    with Cursor() as c:
        c.insert("events", {
            "name": request.json.get("name"),
            "website": request.json.get("website"),
            "league": request.json.get("league"),
            "logo": request.json.get("logo"),
            "splash": request.json.get("splash"),
            "etype": request.json.get("etype"),
            "start_date": from_js_datetime(request.json.get("start_date")),
            "end_date": from_js_datetime(request.json.get("end_date")),
            "active": request.json.get("active")
        })

    return APIResponse()

@admin.route("/api/events/<id>/edit", methods=["POST"])
def admin_event_edit(id):
    updated = EVENT_FIELDS & set(request.json.keys())
    data = {}

    for entry in updated:
        data[entry] = request.json.get(entry)

        if entry.endswith("_date"):
            data[entry] = from_js_datetime(data[entry])

    with Cursor() as c:
        c.update("events", id, data)

    return APIResponse()

@admin.route("/api/news/create", methods=['POST'])
def admin_api_create_news_post():
    return APIResponse({
        "id": create_news_post(
            request.json['title'],
            request.json['category'],
            request.json['content'],
            request.json.get("meta", {}),
            request.json['is_public'],
            g.user)
    })

@admin.route("/api/news/<int:newspost_id>/edit", methods = ['POST'])
def admin_api_edit_news_post(newspost_id):
    update_news_post(
        request.json['id'],
        request.json['title'],
        request.json['category'],
        request.json['content'],
        request.json.get("meta", {}),
        request.json['is_public'])

    return APIResponse()

BANS_LIST_QUERY = """
SELECT * FROM bans ORDER BY id ASC LIMIT %s OFFSET %s
"""

@admin.route("/api/ban/list")
@authed(UserGroup.ADMIN, api=True)
def admin_list_bans():
    page = int(request.values.get("page", 1 ))

    g.cursor.execute("SELECT count(*) as c FROM bans")

    pages = (g.cursor.fetchone().c / 50) + 1

    g.cursor.execute(BANS_LIST_QUERY, paginate(page, per_page=50))
    bans = [];

    for entry in g.cursor.fetchall():
        bans.append({
            "id": entry.id,
            "steamid": entry.steamid,
            "active": entry.active,
            "created_at": entry.created_at.isoformat(),
            "start_date": entry.start_date.isoformat(),
            "end_date": entry.end_date.isoformat(),
            "reason": entry.reason,
            "description": entry.description,
            "created_by": entry.created_by
        })

    return APIResponse({"bans": bans, "pages":pages})

@admin.route("/api/ban/create", methods=["POST"])
@authed(UserGroup.ADMIN, api=True)
def admin_create_ban():
    with Cursor() as c:
        c.insert("bans", {
            "steamid": request.values['steamid'],
            "active": True,
            "created_at": datetime.utcnow(),
            "created_by": g.user,
            "start_date": request.values['start_date'],
            "end_date": request.values['end_date'],
            "reason": request.values['reason'],
            "description": request.values['description']
        })

        # If we have a user with that steamid, invalidate all sessions for them
        u = c.execute("SELECT id FROM users WHERE steamid=%s",
            (request.values['steamid'], )).fetchone()

        if u:
            map(lambda i: i.end(), find_sessions_for_user(u.id))

    return APIResponse()

BAN_EDITABLE_FIELDS = [
    "start_date", "end_date", "reason", "description", "active"
]

@admin.route("/api/ban/edit", methods=["POST"])
@authed(UserGroup.ADMIN, api=True)
def admin_edit_ban():
    ban = request.values.get("id")

    modified_fields = {k: v for (k, v) in request.values.iteritems() if k in BAN_EDITABLE_FIELDS}
    if not len(modified_fields):
        raise APIError("Nothing to change!")

    with Cursor() as c:
        c.update("bans", ban, modified_fields)

    return APIResponse({
        "fields": modified_fields.keys()
    })

