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

def match_to_json(m):
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

    # This will most definitily require some fucking caching at some point
    c.execute("SELECT * FROM bets WHERE match=%s", (m.id, ))
    bets = c.fetchall()

    match['value'] = sum(map(lambda i: i.value, bets))
    match['bets'] = len(bets)

    # Grab team information, including bets (this should be a join)
    c.execute("SELECT * FROM teams WHERE id IN %s", (tuple(m.teams), ))
    teams = c.fetchall()

    for index, team in enumerate(teams):
        team_data = {
            "id": team.id,
            "name": team.name,
            "tag": team.tag,
            "logo": team.logo,
        }

        team_bets = filter(lambda i: i.team == team.id, bets)
        team_data['bets'] = len(team_bets)
        team_data['value'] = sum(map(lambda i: i.value, team_bets))

        # TODO: do this shit
        team_data['payout'] = 0
        team_data['odds'] = 0

        match['teams'].append(team_data)

    for key in ['league', 'type', 'event', 'streams']:
        if key in m.meta:
            match['extra'][key] = m.meta[key]

    match['results'] = m.results
    return match

