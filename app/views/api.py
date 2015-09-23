import json, requests

from collections import defaultdict

from cStringIO import StringIO
from datetime import datetime
from flask import Blueprint, request, g, send_file, redirect, flash

from database import Cursor, redis

from helpers.match import match_to_json
from helpers.bot import get_bot_space, create_bot_item_transfer, create_return_trade
from helpers.bet import BetState, create_bet, find_avail_bot
from helpers.user import (UserGroup, gache_user_info, user_save_settings,
    authed, USER_SETTING_SAVE_PARAMS)
from helpers.team import team_to_json

from helpers.common import get_enum_array
from helpers.news import newspost_to_json
from helpers.trade import get_trade_notify_content
from helpers.stats import value_history_to_json

from tasks.trades import push_trade
from tasks.inventory import push_steam_inventory

from util import paginate
from util.errors import (
    FortException, UserError, APIError, InvalidRequestError, InvalidTradeUrl,
    apiassert)
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

@api.route("/flash")
def route_flash():
    flash(request.values.get("msg"), request.values.get("type", "success"))
    return APIResponse()



    

MATCH_LIST_QUERY = """
SELECT {} FROM matches
WHERE now() > public_date AND active=true
ORDER BY match_date LIMIT %s OFFSET %s
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
    except FortException:
        raise APIError("Invalid match ID")

MATCH_SWITCH_BET_FIELDS = [
    "id", "teams", "match_date", "public_date", "active"
]

@api.route("/match/<int:match_id>/switchteam", methods=["POST"])
@authed()
def route_switch_team(match_id):
    # Get the match.
    match = g.cursor.select("matches", *MATCH_SWITCH_BET_FIELDS, id=match_id).fetchone()

    # Ensure it is a valid match and a bet change is still allowed
    apiassert(match, "Invalid Match ID")
    apiassert(match.active, "Invalid Match ID")
    apiassert(match.public_date.replace(tzinfo=None) < datetime.utcnow(), "Invalid Match ID")

    # Find the bet
    g.cursor.execute("""
        SELECT id, team FROM bets WHERE better=%s AND match=%s AND state!='CANCELLED'
    """, (g.user, match.id))

    bet = g.cursor.fetchone()

    if not bet:
        raise APIError("Switch Team Failed, Bet not Found")

    # Find the other team
    newteam = 0

    if bet.team == match.teams[0]:
        newteam = match.teams[1]
    else:
        newteam = match.teams[0]

    #Update the bet
    g.cursor.execute("UPDATE bets SET team=%s WHERE id=%s", (newteam, bet.id))

    return APIResponse()

MATCH_CONFIRM_BET_FIELDS = [
    "id", "state", "itemstate", "teams", "match_date", "public_date", "active",
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
    apiassert(0 < len(items) <= 4, "Invalid Items")

    # Make sure the user doesn't have any other pending trades
    g.cursor.execute("SELECT id FROM trades WHERE user_ref=%s AND state < 'ACCEPTED'", (g.user, ))
    if g.cursor.fetchone():
        raise APIError("You already have a bet with a pending trade offer! Please accept that before creating more bets.")

    # Grab some info for the match
    match = g.cursor.select("matches", *MATCH_CONFIRM_BET_FIELDS, id=match_id).fetchone()

    # Grab prices for the items placed
    dbitems = g.cursor.execute("SELECT name, price FROM items WHERE id IN %s",
        (tuple(items), )).fetchall(as_list=True)

    if len(dbitems) != len(items):
        raise APIError("Invalid Items")

    # Make sure the price is right
    max_value = match.max_value_item or 73
    for item in dbitems:
        apiassert(item.price < max_value, "Price of item %s is too high" % item.name)

    bet_total = sum(map(lambda i: i.price, dbitems))
    apiassert(bet_total > .50, "Total value placed is too low!")
    apiassert(bet_total < (match.max_value_total or 300), "Total value placed is too high!")

    # Make sure we have a valid match
    apiassert(match, "Invalid match ID")
    apiassert(match.active, "Invalid match ID")
    apiassert(match.public_date.replace(tzinfo=None) < datetime.utcnow(), "Invalid match ID")
    apiassert(match.state == "OPEN", "Match is locked")
    apiassert(match.itemstate == "OPEN", "Match is locked")
    apiassert(team in match.teams, "Invalid Team")

    # Make sure this user doesn't already have a bet on this match
    g.cursor.execute("SELECT * FROM bets WHERE better=%s AND match=%s AND state>='CONFIRMED'",
        (g.user, match.id))
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

GET_TEAMS_SQL = """
SELECT * FROM teams
"""
@api.route("/team/list")
def route_team_list():
    #TODO check if the user's allowed sharing of their history
    teams = g.cursor.execute(GET_TEAMS_SQL).fetchall()
    return APIResponse({"teams":map(team_to_json, teams)})

@api.route("/team/<int:id>/info")
def route_team_info():
    pass


@api.route("/user/inventory")
@authed(api=True)
def route_user_inventory():
    with Cursor() as c:
        push_steam_inventory.queue(g.user)
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
                "returns": get_returns(g.user, entry.match),
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

        data = gache_user_info(user.steamid)

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
    except InvalidTradeUrl as e:
        raise APIError("Invalid Trade URL, %s" % e.msg)

    return APIResponse()

@api.route("/item/image/<id>")
def route_item_image(id):
    item = g.cursor.execute("SELECT image FROM items WHERE id=%s", (id, )).fetchone()
    return redirect("https://steamcommunity-a.akamaihd.net/economy/image/%s" % item.image)

def get_returns(user, match=None):
    with Cursor() as c:
        extra = ""

        if match:
            extra = " AND r.match=%(match)s"

        c.execute("""
            SELECT r.id as return_id, i.id, i.image, i.price, b.id as bot FROM returns r
            JOIN itemprices ip ON ip.id=r.item_type
            JOIN items i ON (i.name=ip.name AND i.state='INTERNAL')
            JOIN bots b ON b.steamid=i.owner
            WHERE r.state='PENDING' AND r.owner=%(owner)s {}
            FOR UPDATE
        """.format(extra), {
            "owner": user,
            "match": match,
        })

        return c.fetchall(as_list=True)

@api.route("/returns/list")
def route_returns_list():
    with Cursor() as c:
        returns = []
        for entry in get_returns(g.user):
            returns.append({
                "id": entry.id,
                "image": entry.image,
                "price": entry.price
            })

        return APIResponse({
            "returns": returns
        })

@api.route("/returns/match/<id>/request", methods=['POST'])
def route_returns_match_request(id):
    with Cursor() as c:
        c.execute("SELECT id FROM trades WHERE user_ref=%s AND state < 'ACCEPTED'", (g.user, ))
        if c.fetchone():
            raise APIError("You already have a bet with a pending trade offer! Please accept that before creating more bets.")

        # Grab the returns
        returns = get_returns(g.user, match=id)

        trades = defaultdict(list)
        for entry in returns:
            trades[entry.bot].append(entry)

        offers = []
        for bot, returns in trades.items():
            id = create_return_trade(bot, g.user, map(lambda i: i.id, returns))

            for ret in returns:

                c.update("returns", ret.return_id, trade=id)

            offers.append(id)

    map(push_trade.queue, offers)
    return APIResponse({
        "offers": offers,
    })

# TODO: This is also in admin.py, it really really needs to go into a helper file.
# Once all base functionality is complete I'll go throught and refactor as much as I can.
# Also, this
EVENT_FIELDS = { "name", "website", "league", "logo", "splash", "etype", "start_date", "end_date" }
EVENT_LIST_QUERY = "SELECT * FROM events {} ORDER BY id LIMIT %s OFFSET %s;"

@api.route("/events/list", methods=["POST"])
def api_event_list():
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

EVENT_MATCH_LIST_QUERY = """
SELECT * FROM matches
WHERE now() > public_date AND active=true AND event={0}
ORDER BY match_date
"""

@api.route("/events/<int:id>/list")
def route_event_match_list(id):
    g.cursor.execute(EVENT_MATCH_LIST_QUERY.format(id))

    matches = map(match_to_json, g.cursor.fetchall())

    return APIResponse({
        "matches": matches
    })

@api.route("/news/<int:id>", methods = ['GET'])
def api_get_news_post(id):
    g.cursor.execute("""
        SELECT ns.*, u.steamid FROM newsposts ns
        LEFT JOIN users u ON u.id=ns.created_by
        WHERE (ns.is_public=true or %s) AND ns.id=%s
    """, (((g.group or 0) >= UserGroup.ADMIN), id))
    post = g.cursor.fetchone()

    if not post:
        raise APIError("Couldn't Find News Post: {0}".format(id))

    return APIResponse({
        "post": newspost_to_json(post)
    })

@api.route("/news/list", methods = ['GET'])
def api_get_news_posts():
    g.cursor.execute("""
        SELECT ns.*, u.steamid FROM newsposts ns
        LEFT JOIN users u ON u.id=ns.created_by
        WHERE (ns.is_public=true OR %s) ORDER BY ns.created_at LIMIT 100
    """, (((g.group or 0) >= UserGroup.ADMIN), ))

    return APIResponse({
        "posts": map(newspost_to_json, g.cursor.fetchall())
    })

@api.route("/trade/pending", methods=["GET"])
@authed()
def api_get_trade_list():
    trade = g.cursor.execute("""
        SELECT id FROM trades
        WHERE user_ref=%s AND state='OFFERED'
        LIMIT 1
    """, (g.user, )).fetchone()

    if not trade:
        return APIResponse({"trade": None})

    return APIResponse({"trade": get_trade_notify_content(trade.id)[1]})

@api.route("/stats/value/history", methods=["GET"])
def route_stats_overview():
    #TODO check if the user's allowed sharing of their history
    if request.values.get('id'):
        user = request.values.get('id')
    else:
        user = g.user

    if not isinstance(user, int) and not user.isdigit():
        return APIResponse({"success":"false"});
    
    query = g.cursor.mogrify("""
    SELECT bets.value, bets.team, matches.match_date, (bets.team=(matches.results->'winner')::text::int) as won, matches.id FROM matches JOIN bets ON matches.id=bets.match WHERE bets.better=%s AND matches.results->'winner'::text != 'null' ORDER BY matches.match_date
    """, (user, ))
    stats = g.cursor.execute(query).fetchall()
    return APIResponse({"history":map(value_history_to_json, stats)})
