from datetime import datetime
from collections import namedtuple
from psycopg2.extras import Json
from flask import g

from database import Cursor
from util.errors import InvalidRequestError, ValidationError
from helpers.user import UserGroup

CREATE_MATCH_SQL = """
INSERT INTO matches (game, teams, meta, results, lock_date, match_date, public_date, view_perm, active, created_at, created_by)
VALUES (%(game)s, %(teams)s, %(meta)s, %(results)s, %(lock_date)s, %(match_date)s, %(public_date)s,
%(view_perm)s, %(active)s, %(created_at)s, %(created_by)s)
RETURNING id
"""

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

def validate_match_meta_data(obj):
    if not isinstance(obj, dict):
        raise ValidationError("Match meta data must be a dictionary")

    return True

def create_match(user, game, teams, meta, lock_date, match_date, public_date, view_perm=UserGroup.NORMAL):
    validate_match_team_data(teams)

    with Cursor() as c:
        c.execute(CREATE_MATCH_SQL, {
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


MATCH_SELECT_SQL = "SELECT * FROM matches WHERE id=%s"

def match_to_json(m, user=None):
    """
    Right now this function is a performance clusterfuck. Almost all of the data in
    here can be gathered with a single query and windowed multi-join, but lets wait
    until shit breaks, eh?
    """
    c = Cursor()

    if not isinstance(m, tuple):
        c.execute(MATCH_SELECT_SQL, (m, ))
        m = c.fetchone()

    if not m:
        raise InvalidRequestError("Failed to match_to_json with arg %s" % m)

    match = {}

    match['id'] = m.id
    match['game'] = m.game
    match['when'] = int(m.match_date.strftime("%s"))
    match['teams'] = []
    match['extra'] = {}
    match['stats'] = {}

    if user:
        match['me'] = {}

        mybet = c.execute("""
            SELECT id, team, items::steam_item[], state, value FROM bets WHERE match=%s AND better=%s
        """, (m.id, user)).fetchone()

        if mybet:
            match['me']['id'] = mybet.id
            match['me']['team'] = mybet.team
            match['me']['items'] = map(lambda i: i.to_string(), mybet.items)
            match['me']['state'] = mybet.state
            match['me']['value'] = mybet.value

    # This will most definitily require some fucking caching at some point
    bet_stats = c.execute("""SELECT
            sum(array_length(items, 1)) as skins_count,
            count(*) as count,
            sum(value) as value,
            team
        FROM bets WHERE match=%s GROUP BY team""", (m.id, )).fetchall(as_list=True)

    match['stats']['players'] = sum(map(lambda i: i.count, bet_stats))
    match['stats']['skins'] = sum(map(lambda i: i.skins_count, bet_stats))
    match['stats']['value'] = sum(map(lambda i: i.value, bet_stats))
    bet_stats = { i.team: i for i in bet_stats}

    # Grab team information, including bets (this should be a join)
    c.execute("SELECT * FROM teams WHERE id IN %s", (tuple(m.teams), ))
    teams = c.fetchall()

    for index, team in enumerate(teams):
        team_data = {
            "id": team.id,
            "name": team.name,
            "tag": team.tag,
            "logo": team.logo,
            "stats": {
                "players": 0,
                "skins": 0,
                "value": 0,
            }
        }

        if index in bet_stats:
            team_data['stats']['players'] = bet_stats[index].count
            team_data['stats']['skins'] = bet_stats[index].skins_count
            team_data['stats']['value'] = bet_stats[index].value

        # TODO: do this shit
        team_data['payout'] = 0
        team_data['odds'] = 0

        match['teams'].append(team_data)

    for key in ['league', 'type', 'event', 'note']:
        if key in m.meta:
            match['extra'][key] = m.meta[key]

    match['results'] = m.results
    return match

