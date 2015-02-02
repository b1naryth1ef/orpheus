import json

from datetime import datetime
from flask import Blueprint, request, g

from database import Cursor

from helpers.match import match_to_json
from helpers.bot import get_bot_space
from helpers.bet import create_bet

from util.etc import paginate
from util.perms import authed
from util.queue import JobQueue
from util.errors import UserError, APIError, InvalidRequestError, apiassert
from util.responses import APIResponse

api = Blueprint("api", __name__, url_prefix="/api")

@api.route("/status")
def route_status():
    try:
        g.cursor.execute("SELECT 1 AS v;")
        res = g.cursor.fetchone()
        assert(res.v == 1)
    except:
        raise APIError("Site is currently experiencing issues.")
    return APIResponse()

@api.route("/stats/overview")
def route_stats_overview():
    pass

MATCH_LIST_QUERY = """
SELECT * FROM matches
WHERE now() > public_date AND active=true
ORDER BY id LIMIT %s OFFSET %s
"""

@api.route("/match/list")
def route_match_list():
    page = int(request.values.get("page", 1))

    pages = (g.cursor.count("matches", "now() > public_date AND active=true") / 25) + 1
    g.cursor.execute(MATCH_LIST_QUERY, paginate(page, per_page=25))
    matches = map(match_to_json, g.cursor.fetchall())

    return APIResponse({
        "matches": matches
    })

@api.route("/match/<int:id>/info")
def route_match_info(id):
    try:
        match = match_to_json(id, user=g.user)
        return APIResponse({
            "match": match
        })
    except InvalidRequestError:
        raise APIError("Invalid match ID")

@api.route("/match/<int:match_id>/bet", methods=["POST"])
@authed()
def route_match_bet(match_id):
    try:
        items = json.loads(request.values.get("items"))
        team = int(request.values.get("team"))
    except Exception as e:
        raise APIError("Invalid Request: %s" % e)

    # Make sure this seems mildly valid
    apiassert(0 < len(items) <= 4, "Too many items")
    print items
    apiassert(all(map(lambda i: i.isdigit(), items)), "Invalid Items")

    match = g.cursor.select("matches",
        "id", "teams", "lock_date", "match_date", "public_date", "active", id=match_id).fetchone()

    # Make sure we have a valid match
    apiassert(match, "Invalid match ID")
    apiassert(match.active, "Invalid match ID")
    apiassert(match.public_date.replace(tzinfo=None) < datetime.utcnow(), "Invalid match ID")
    apiassert(match.lock_date.replace(tzinfo=None) > datetime.utcnow(), "Match is locked")
    apiassert(len(match.teams) > team, "Invalid Team")

    # Make sure this user doesn't already have a bet on this match
    g.cursor.execute("SELECT * FROM bets WHERE better=%s AND match=%s", (g.user, match.id))
    apiassert(g.cursor.fetchone() == None, "Bet already created")

    # Ensure we have space for the items
    used, avail = get_bot_space()
    apiassert(avail > len(items), "No space left for bet")

    return APIResponse({
        "bet": create_bet(g.user, match_id, team, items)
    })

GET_GAMES_SQL = """
SELECT id, name, appid FROM games
WHERE view_perm >= %s AND active = true
"""

@api.route("/game/list")
def route_game_list():
    g.cursor.execute(GET_GAMES_SQL, (g.group, ))

    results = []
    for entry in g.cursor.fetchall():
        results.append({
            "id": entry.id,
            "name": entry.name,
            "appid": entry.appid
        })

    return APIResponse({
        "games": results
    })

@api.route("/game/<int:id>/info")
def route_game_info():
    pass

@api.route("/team/list")
def route_team_list():
    pass

@api.route("/team/<int:id>/info")
def route_team_info():
    pass


@api.route("/user/inventory")
@authed(api=True)
def route_user_inventory():
    with Cursor() as c:
        user = c.execute("SELECT steamid FROM users WHERE id=%s", (g.user, )).fetchone()

        if not user:
            raise APIError("Invalid User ID")

        JobQueue("inventory").fire({"steamid": user.steamid, "user": g.user})
        return APIResponse()

