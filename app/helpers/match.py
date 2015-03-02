from datetime import datetime
from collections import namedtuple
from psycopg2.extras import Json
from flask import g

from database import Cursor
from util.errors import InvalidRequestError, ValidationError, FortException
from helpers.user import UserGroup
from helpers.bet import BetState

def validate_match_team_data(obj):
    if not isinstance(obj, list):
        raise ValidationError("Team data must be a list")

    if not len(obj) > 2:
        raise ValidationError("Team data must containt at least two teams")

    if not all(map(lambda i: i.get("name"), obj)):
        raise ValidationError("Teams in team data must contain at least a name")

    if not all(map(lambda i: isinstance(i.get("players"), list), obj)):
        raise ValidationError("Teams must have a list of players (can be empty")

    return True

def create_match(user, game, teams, meta, lock_date, match_date, public_date,
        view_perm=UserGroup.NORMAL):

    # Make sure the teams are valid
    validate_match_team_data(teams)

    # Make sure meta info is valid
    if not isinstance(meta, dict):
        raise ValidationError("Match meta data must be a dictionary")

    with Cursor() as c:
        c.insert("matches", {
            "game": game,
            "teams": teams,
            "meta": meta,
            "results": Cursor.json({}),
            "lock_date": lock_date,
            "match_date": match_date,
            "public_date": public_date,
            "view_perm": view_perm,
            "active": False,
            "created_at": datetime.utcnow(),
            "created_by": user
        })

        return c.fetchone().id

# This query gets all items pertaining to a match (e.g. winnings or items placed)
MATCH_GET_ITEMS_QUERY = """
SELECT i.id, i.type_id, i.price, i.meta, it.name as name FROM
    (SELECT unnest(array_cat(b.items, b.winnings)) AS item_id FROM bets b WHERE b.id=%s) b
JOIN items i ON i.id=item_id
JOIN itemtypes it ON it.id=i.type_id;
"""

# Select some information about bets for this match
MATCH_GET_BETS_INFO_QUERY = """
SELECT
    sum(array_length(items, 1)) as skins_count,
    count(*) as count,
    sum(value) as value,
    team
FROM bets WHERE match=%s AND state >= 'CONFIRMED' GROUP BY team
"""

def match_to_json(m, user=None):
    """
    Right now this function is a performance clusterfuck. Almost all of the data in
    here can be gathered with a single query and windowed multi-join, but lets wait
    until shit breaks, eh?
    """
    c = Cursor()

    if not isinstance(m, tuple):
        c.execute("SELECT {} FROM matches WHERE id=%s".format(
            ', '.join(match_to_json.required_fields)), (m, ))
        m = c.fetchone()

    if not m:
        raise FortException("Failed to match_to_json with arg %s" % m)

    event = c.execute("SELECT * FROM events WHERE id=%s", (m.event, )).fetchone()
    if not event:
        raise FortException("Could not find event for match")

    match = {}
    match['id'] = m.id
    match['state'] = m.state
    match['itemstate'] = m.itemstate
    match['game'] = m.game
    match['when'] = int(m.match_date.strftime("%s"))
    match['public'] = int(m.public_date.strftime("%s"))
    match['active'] = m.active
    match['teams'] = {}
    match['extra'] = {}
    match['stats'] = {}

    match['event'] = {
        "id": event.id,
        "name": event.name,
        "website": event.website,
        "league": event.league,
        "logo": event.logo,
        "splash": event.splash,
        "streams": event.streams,
        "games": event.games,
        "type": event.etype
    }

    # This will most definitily require some fucking caching at some point
    bet_stats = c.execute(MATCH_GET_BETS_INFO_QUERY, (m.id, )).fetchall(as_list=True)

    match['stats']['players'] = sum(map(lambda i: i.count, bet_stats))
    match['stats']['skins'] = sum(map(lambda i: i.skins_count, bet_stats))
    match['stats']['value'] = sum(map(lambda i: i.value, bet_stats))
    bet_stats = { i.team: i for i in bet_stats}

    # Grab team information, including bets (this should be a join)
    c.execute("SELECT id, name, tag, logo FROM teams WHERE id IN %s", (tuple(m.teams), ))
    teams = c.fetchall()

    total_bets = sum(map(lambda i: i.count, bet_stats.values())) * 1.0
    total_value = sum(map(lambda i: i.value, bet_stats.values()))

    values = {}

    for team in teams:
        team_data = {
            "id": team.id,
            "name": team.name,
            "tag": team.tag,
            "logo": team.logo,
            "stats": {
                "players": 0,
                "skins": 0,
                "value": 0,
            },
            "odds": 0
        }

        if team.id in bet_stats:
            team_data['stats']['players'] = bet_stats[team.id].count
            team_data['stats']['skins'] = bet_stats[team.id].skins_count
            team_data['stats']['value'] = bet_stats[team.id].value
            team_data['odds'] = float("{0:.2f}".format(bet_stats[team.id].count / total_bets))
            values[team.id] = bet_stats[team.id].value

        match['teams'][team.id] = team_data

    if user:
        match['me'] = {}

        # Get any bets I placed
        mybet = c.execute("""
            SELECT id, items, winnings, team, state, value FROM bets
            WHERE match=%s AND better=%s AND state != 'CANCELLED'
        """, (m.id, user)).fetchone()

        if mybet:
            items = c.execute(MATCH_GET_ITEMS_QUERY, (mybet.id, )).fetchall()

            match['me']['id'] = mybet.id
            match['me']['team'] = mybet.team
            match['me']['state'] = mybet.state
            match['me']['value'] = mybet.value
            match['me']['state'] = mybet.state

            if total_value > mybet.value and mybet.team in values:
                my_return = ((float(total_value) * 1.0) / float(values[mybet.team])) * float(mybet.value)
            else:
                my_return = mybet.value

            match['me']['return'] = float("{0:.2f}".format(my_return))

            # Load items in sub query :(
            match['me']['items'] = []
            match['me']['winnings'] = []

            for item in items:
                data = {
                    "id": item.id,
                    "name": item.name,
                    "price": item.price,
                    "image": item.meta['image'],
                }

                if item.id in mybet.items:
                    match['me']['items'].append(data)

                if item.id in (mybet.winnings or []):
                    match['me']['winnings'].append(data)

    for key in ['league', 'type', 'event', 'streams', 'maps', 'note']:
        if key in m.meta:
            match['extra'][key] = m.meta[key]

    match['extra']['brief'] = ' vs '.join(map(lambda i: i['tag'], match['teams'].values()))
    match['results'] = m.results
    return match

match_to_json.required_fields = [
    'id', 'game', 'match_date', 'meta', 'results', 'teams', 'state', 'itemstate', 'event',
    'public_date', 'active']

