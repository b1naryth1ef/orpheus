from flask import Blueprint, g

from util.errors import UserError, APIError
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

@api.route("/match/list")
def route_match_list():
    return APIResponse({
        "matches": [
            
        ]
    })

@api.route("/match/<int:id>/info")
def route_match_info(id):
    pass

@api.route("/game/list")
def route_game_list():
    pass

@api.route("/game/<int:id>/info")
def route_game_info():
    pass

@api.route("/team/list")
def route_team_list():
    pass

@api.route("/team/<int:id>/info")
def route_team_info():
    pass

