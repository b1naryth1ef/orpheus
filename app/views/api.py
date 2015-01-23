from flask import Blueprint, request, g

from helpers.match import match_to_json
from util.etc import paginate
from util.errors import UserError, APIError, InvalidRequestError
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

    g.cursor.execute("SELECT count(*) as c FROM matches")
    pages = (g.cursor.fetchone().c / 25) + 1

    g.cursor.execute(MATCH_LIST_QUERY, paginate(page, per_page=25))

    return APIResponse({
        "matches": map(match_to_json, g.cursor.fetchall())
    })

@api.route("/match/<int:id>/info")
def route_match_info(id):
    try:
        match = match_to_json(id)
        return APIResponse({
            "match": match
        })
    except InvalidRequestError:
        raise APIError("Invalid match ID")

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

