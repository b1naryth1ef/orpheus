from datetime import datetime
from dateutil.relativedelta import relativedelta
from psycopg2.extras import Json
import json, random, os

cur_dir = os.path.dirname(__file__)

ONE_WEEK_PAST = datetime.utcnow() + relativedelta(weeks=-1)
ONE_WEEK_FUTURE = datetime.utcnow() + relativedelta(weeks=1)

USERS = [
    ("76561198037632722", "SUPER"),
    ("76561198031651584", "NORMAL"),
]

RANDOM_STEAMIDS = json.load(open(os.path.join(cur_dir, "random_steamids.json"), "r"))

def generate_users(t, db):
    for user in USERS:
        t.execute("INSERT INTO users (steamid, active, ugroup) VALUES (%s, %s, %s)",
            (user[0], True, user[1]))

    for steamid in RANDOM_STEAMIDS:
        t.execute("INSERT INTO users (steamid, active, ugroup) VALUES (%s, %s, %s)",
            (steamid, True, "NORMAL"))

GAME = {
    "name": "CS:GO",
    "appid": 730,
    "active": True,
}

def generate_games(t, db):
    t.execute("INSERT INTO games (name, appid, active) VALUES (%(name)s, %(appid)s, %(active)s)",
        GAME)

TEAMS = [
    ("c9", "Cloud9", "/static/img/teams/cloud9.png"),
    ("fnatic", "Fnatic", "/static/img/teams/fnatic.png"),
    ("HellRaisers", "HellRaisers", "/static/img/teams/hellraisers.png"),
    ("dignitas", "Team Dignitas", "/static/img/teams/dignitas.png"),
    ("nip", "Ninjas In Pajamas", "/static/img/teams/nip.png"),
    ("virtus.pro", "Virtus Pro", "/static/img/teams/virtuspro.png"),
    ("CLG", "Counter Logic Gaming", "http://clgaming.net/interface/img/ogImage.jpg")
]

def generate_teams(t, db):
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
                "splash": "http://i.imgur.com/x9zkVjg.png",
                "logo": "http://i.imgur.com/8VIcWM2.png"
            },
            "type": "BO1",
            "streams": ["http://twitch.tv/test1", "http://twitch.tv/test2"],
            "maps": ["de_nuke"]
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
            "note": "This is a test note!",
            "type": "BO3",
            "streams": ["http://mlg.tv/swag", "http://twitch.tv/esea"],
            "maps": ["de_nuke", "de_mirage", "de_dust2"]
        },
        "lock_date": ONE_WEEK_FUTURE,
        "match_date": ONE_WEEK_FUTURE,
        "public_date": datetime.utcnow()
    },
    {
        "game": 1,
        "teams": [5, 6],
        "meta": {
            "league": {
                "name": "ESL Katowice",
                "info": None,
                "splash": "http://i.imgur.com/YHUUssh.png",
                "logo": "http://i.imgur.com/YHUUssh.png"
            },
            "type": "BO3",
            "streams": ["http://mlg.tv/swag", "http://twitch.tv/esea"],
            "maps": ["de_facade", "de_mirage", "de_dust2"]
        },
        "lock_date": ONE_WEEK_PAST,
        "match_date": ONE_WEEK_PAST,
        "public_date": ONE_WEEK_PAST,
    }
]

MATCH_QUERY = """
INSERT INTO matches (game, teams, meta, lock_date, match_date, public_date, active) VALUES
(%(game)s, %(teams)s, %(meta)s, %(lock_date)s, %(match_date)s, %(public_date)s, true);
"""

def generate_matches(t, db):
    for match in MATCHES:
        match['meta'] = Json(match['meta'])
        t.execute(MATCH_QUERY, match)

betters = range(1, len(RANDOM_STEAMIDS))

BETS = [
    {
        "better": random.randint(1, 10000),
        "match": 1,
        "team": random.choice([1, 2]),
        "value": random.randint(1, 40),
        "items": [(random.randint(1, 25), 'NULL', 'NULL', random.randint(1, 20)) for i in range(4)],
        "state": "confirmed",
        "created_at": datetime.utcnow(),
    } for i in range(2500)
] + [
    {
        "better": betters.pop(0),
        "match": 3,
        "team": random.choice([5, 6]),
        "value": random.randint(1, 40),
        "items": [(random.randint(1, 25), 'NULL', 'NULL', random.randint(1, 20)) for i in range(4)],
        "state": "confirmed",
        "created_at": datetime.utcnow(),
    } for i in range(25000)
]

BET_QUERY = """
INSERT INTO bets (better, match, team, value, items, state, created_at) VALUES
(%(better)s, %(match)s, %(team)s, %(value)s, ARRAY[{}], %(state)s, %(created_at)s);
"""

# TODO
def generate_bets(t, db):
    for index, entry in enumerate(BETS):
        if index % 10000 == 0:
            print "    Bet #%s" % index
            db.commit()
        data = entry['items']
        del entry['items']
        q = BET_QUERY.format(', '.join(map(lambda i: ("(%s, %s, %s, '{\"price\": %s}')" % i) + "::steam_item", data)))
        t.execute(q, entry)

DATA_GENERATORS = [
    generate_users,
    generate_games,
    generate_teams,
    generate_matches,
    generate_bets
]

