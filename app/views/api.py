import json, requests

from cStringIO import StringIO
from datetime import datetime
from flask import Blueprint, request, g, send_file, redirect

from emporium import steam
from database import Cursor, redis

from helpers.match import match_to_json
from helpers.bot import get_bot_space
from helpers.bet import BetState, create_bet
from helpers.user import (UserGroup, gache_user_info, user_save_settings,
    authed, USER_SETTING_SAVE_PARAMS)

from util import paginate
from util.queue import JobQueue
from util.errors import UserError, APIError, InvalidRequestError, InvalidTradeUrl, apiassert
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
SELECT {} FROM matches
WHERE now() > public_date AND active=true
ORDER BY id LIMIT %s OFFSET %s
""".format(', '.join(match_to_json.required_fields))

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

# TODO: deprecate?
@api.route("/match/<int:id>/items")
def route_match_items(id):
    match = g.cursor.select("matches", "id", id=match_id).fetchone()

    if not match:
        return APIError("Invalid match ID")

MATCH_CONFIRM_BET_FIELDS = [
    "id", "teams", "lock_date", "match_date", "public_date", "active",
    "max_value_item", "max_value_total"
]

@api.route("/match/<int:match_id>/bet", methods=["POST"])
@authed()
def route_match_bet(match_id):
    try:
        items = map(int, json.loads(request.values.get("items")))
        team = int(request.values.get("team"))
    except Exception as e:
        raise APIError("Invalid Request: %s" % e)

    # Need a trade token
    user_to = g.cursor.select("users", "trade_token", id=g.user).fetchone()
    if not user_to.trade_token:
        raise APIError("You must set a trade token to bet!")

    # Make sure this seems mildly valid
    apiassert(0 < len(items) <= 4, "Too many items")

    # Grab some info for the match
    match = g.cursor.select("matches", *MATCH_CONFIRM_BET_FIELDS, id=match_id).fetchone()

    # Make sure we haven't bet too much shit
    if match.max_value_item:
        for item in itemvs:
            apiassert(item.price < match.max_value_item, "Price of item %s is too high!" % item.name)

    if match.max_value_total:
        apiassert(sum(map(lambda i: i.price, itemvs)) < match.max_value_total, "Total value placed is too high!")

    # Make sure we have a valid match
    apiassert(match, "Invalid match ID")
    apiassert(match.active, "Invalid match ID")
    apiassert(match.public_date.replace(tzinfo=None) < datetime.utcnow(), "Invalid match ID")
    apiassert(match.lock_date.replace(tzinfo=None) > datetime.utcnow(), "Match is locked")
    apiassert(team in match.teams, "Invalid Team")

    # Make sure this user doesn't already have a bet on this match
    g.cursor.execute("SELECT * FROM bets WHERE better=%s AND match=%s AND state>='CONFIRMED'", (g.user, match.id))
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

USER_BETS_QUERY = """
SELECT b.id, b.match, b.team, b.value, b.state, b.winnings, b.items, m.id AS mid, m.teams, m.results,
    t.offerid AS t_offerid, t.state AS t_state
FROM bets b
JOIN matches m ON m.id = match
JOIN trades t ON t.bet_ref = b.id
WHERE b.better=%s AND b.state != 'CANCELLED'
ORDER BY b.created_at LIMIT 250
"""

@api.route("/user/<int:id>/info")
def route_user_info(id):
    with Cursor() as c:
        user = c.execute("SELECT steamid FROM users WHERE id=%s", (id, )).fetchone()
        bets = c.execute(USER_BETS_QUERY, (id, )).fetchall(as_list=True)

        info = gache_user_info(user.steamid)

        base = {
            "id": id,
            "username": info.get("personaname"),
            "bets": {
                "placed": len(bets),
                "won": len(filter(lambda i: i.state == BetState.WON, bets)),
                "lost": len(filter(lambda i: i.state == BetState.LOST, bets)),
                "detail": []
            }
        }

        if g.user != id:
            return APIResponse(base)

        for entry in bets:
            base['bets']['detail'].append({
                "id": entry.id,
                "match": match_to_json(entry.mid, g.user),
                "team": entry.team,
                "state": entry.state,
                "winnings": entry.winnings,
                "items": entry.items,
                "trade": {
                    "offer": entry.t_offerid,
                    "state": entry.t_state
                }
            })

        return APIResponse(base)

@api.route("/user/<int:id>/avatar")
def auth_route_avatar(id):
    key = "avatar:%s" % id
    if redis.exists(key):
        buffered = StringIO(redis.get(key))
    else:
        with Cursor() as c:
           user = c.execute("SELECT steamid FROM users WHERE id=%s", (id, )).fetchone()

           if not user:
               raise APIError("Invalid User ID")

        data = steam.getUserInfo(user.steamid)

        try:
            r = requests.get(data.get('avatarfull'))
            r.raise_for_status()
        except Exception:
            return "", 500

        # Cached for 1 hour
        buffered = StringIO(r.content)
        redis.setex(key, r.content, (60 * 60))

    buffered.seek(0)
    return send_file(buffered, mimetype="image/jpeg")

@api.route("/user/settings/save", methods=['POST'])
def user_settings_save():
    try:
        sent_data = json.loads(request.values.get("data", "{}"))
    except:
        raise APIError("Failed to decode object")

    data_to_save = {}

    for entry in USER_SETTING_SAVE_PARAMS:
        if entry in sent_data:
            data_to_save[entry] = sent_data[entry]

    apiassert(len(data_to_save) == len(USER_SETTING_SAVE_PARAMS), "Invalid Params")

    try:
        user_save_settings(g.user, data_to_save)
    except InvalidTradeUrl:
        raise APIError("Invalid Trade URL")

    return APIResponse()

@api.route("/item/image/<id>")
def route_item_image(id):
    image = g.cursor.execute("SELECT meta->'image' as i FROM items WHERE id=%s", (id, )).fetchone()
    return redirect("https://steamcommunity-a.akamaihd.net/economy/image/%s" % image.i)

