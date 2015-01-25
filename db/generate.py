from datetime import datetime
from dateutil.relativedelta import relativedelta
from psycopg2.extras import Json

ONE_WEEK_FUTURE = datetime.utcnow() + relativedelta(weeks=1)

ACCOUNTS = [
    ("76561198172199447", "csgoebot1", "password", True)
]

def generate_accounts(t):
    for acc in ACCOUNTS:
        t.execute(
        "INSERT INTO accounts (steamid, username, password, inventory, active, status)\
        VALUES (%s, %s, %s, ARRAY[(1, 1)::steam_item], %s, 'AVAIL')",
            acc)

USERS = [
    ("76561198037632722", "super"),
    ("76561198031651584", "normal"),
]

def generate_users(t):
    for user in USERS:
        t.execute("INSERT INTO users (steamid, active, ugroup) VALUES (%s, %s, %s)",
            (user[0], True, user[1]))

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
    ("CLG", "Counter Logic Gaming", "http://clgaming.net/interface/img/ogImage.jpg"),
    ("NIP", "Ninjas In Pajamas", "http://i.imgur.com/7jN4sff.png"),
    ("LDLC", "LDLC", "http://i.imgur.com/CaS8bD9.png")
]

def generate_teams(t):
    for team in TEAMS:
        t.execute("INSERT INTO teams (tag, name, logo) VALUES (%s, %s, %s)", team)

MATCHES = [
    {
        "game": 1,
        "teams": [1, 5],
        "meta": {
            "league": {
                "name": "CEVO",
                "info": None,
                "splash": "http://i.imgur.com/V8qBKgK.png",
                "logo": "http://i.imgur.com/8VIcWM2.png"
            },
            "type": "BO1",
            "streams": ["http://twitch.tv/test1", "http://twitch.tv/test2"],
        },
        "lock_date": ONE_WEEK_FUTURE,
        "match_date": ONE_WEEK_FUTURE,
        "public_date": datetime.utcnow()
    },
    {
        "game": 1,
        "teams": [3, 4],
        "meta": {
            "league": {
                "name": "ESEA",
                "info": None,
                "splash": "http://i.imgur.com/cQ88n4A.png",
                "logo": "http://i.imgur.com/KCZZVDH.jpg"
            },
            "type": "BO3",
            "streams": ["http://mlg.tv/swag", "http://twitch.tv/esea"],
        },
        "lock_date": ONE_WEEK_FUTURE,
        "match_date": ONE_WEEK_FUTURE,
        "public_date": datetime.utcnow()
    }
]

MATCH_QUERY = """
INSERT INTO matches (game, teams, meta, lock_date, match_date, public_date, active) VALUES
(%(game)s, %(teams)s, %(meta)s, %(lock_date)s, %(match_date)s, %(public_date)s, true);
"""

def generate_matches(t):
    for match in MATCHES:
        match['meta'] = Json(match['meta'])
        t.execute(MATCH_QUERY, match)

def generate_bets(t):
    pass

DATA_GENERATORS = [
    generate_accounts,
    generate_users,
    generate_games,
    generate_teams,
    generate_matches,
    generate_bets
]

