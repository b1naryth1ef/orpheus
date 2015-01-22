from datetime import datetime
from dateutil.relativedelta import relativedelta
from psycopg2.extras import Json

ONE_WEEK_FUTURE = datetime.utcnow() + relativedelta(weeks=1)

GAME = {
    "name": "CS:GO",
    "appid": 730,
    "active": True,
}

def generate_games(t):
    t.execute("INSERT INTO games (name, appid, active) VALUES (%(name)s, %(appid)s, %(active)s)",
        GAME)

TEAMS = [
    ("c9", "Cloud9", "http://i.imgur.com/HsqnrKf.png"),
    ("torqued", "Torqued", ""),
    ("CLG", "Counter Logic Gaming", ""),
    ("NIP", "Ninjas In Pajamas", ""),
    ("LDLC", "LDLC", "")
]

def generate_teams(t):
    for team in TEAMS:
        t.execute("INSERT INTO teams (tag, name, logo) VALUES (%s, %s, %s)", team)

MATCHES = [
    {
        "game": 1,
        "teams": [1, 2],
        "meta": {
            "league": "CEVO",
            "type": "BO1",
            "streams": ["http://twitch.tv/test1", "http://twitch.tv/test2"],
        },
        "lock_date": ONE_WEEK_FUTURE,
        "match_date": ONE_WEEK_FUTURE,
        "public_date": datetime.utcnow()
    }
]

MATCH_QUERY = """
INSERT INTO matches (game, teams, meta, lock_date, match_date, public_date) VALUES
(%(game)s, %(teams)s, %(meta)s, %(lock_date)s, %(match_date)s, %(public_date)s);
"""

def generate_matches(t):
    for match in MATCHES:
        match['meta'] = Json(match['meta'])
        t.execute(MATCH_QUERY, match)

def generate_bets(t):
    pass

DATA_GENERATORS = [
    generate_games,
    generate_teams,
    generate_matches,
    generate_bets
]

