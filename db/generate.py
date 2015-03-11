from datetime import datetime
from dateutil.relativedelta import relativedelta
from psycopg2.extras import Json
import json, random, os

cur_dir = os.path.dirname(__file__)

ONE_WEEK_PAST = datetime.utcnow() + relativedelta(weeks=-1)
ONE_WEEK_FUTURE = datetime.utcnow() + relativedelta(weeks=1)

# B1NZY_USER = ("76561198037632722", "jSiDJlpo", True, "SUPER")
RANDOM_STEAMIDS = json.load(open(os.path.join(cur_dir, "data/random_steamids.json"), "r"))[:30000]

def generate_bots(t, db):
    with open("data/devbots.sql") as f:
        t.execute(f.read())

def generate_users(t, db):
    for steamid in RANDOM_STEAMIDS:
        t.execute("INSERT INTO users (steamid, active, ugroup) VALUES (%s, %s, %s)",
            (steamid, True, "NORMAL"))

GAMES = [
    {
        "name": "CS:GO",
        "appid": 730,
        "active": True,
    }
]

def generate_games(t, db):
    for game in GAMES:
        t.execute("INSERT INTO games (name, appid, active) VALUES (%(name)s, %(appid)s, %(active)s)", game)

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

EVENTS = [
    ('ESEA Invite Season 18',
        'http://play.esea.net/index.php?s=league&d=standings&division_id=2428',
        'ESEA', 'http://i.imgur.com/KCZZVDH.jpg', 'http://i.imgur.com/cQ88n4A.png',
        ['twitch.tv/ESEA'], [1], 'SEASON', datetime.utcnow()),
    ('ESEA Premier Season 18',
        'http://play.esea.net/index.php?s=league&d=standings&division_id=2429',
        'ESEA', 'http://i.imgur.com/KCZZVDH.jpg', 'http://i.imgur.com/cQ88n4A.png',
        ['twitch.tv/ESEA'], [1], 'SEASON', datetime.utcnow()),
    ('ESEA Main Season 18',
        'http://play.esea.net/index.php?s=league&d=standings&division_id=2430',
        'ESEA', 'http://i.imgur.com/KCZZVDH.jpg', 'http://i.imgur.com/cQ88n4A.png',
        ['twitch.tv/ESEA'], [1], 'SEASON', datetime.utcnow()),
    ('ESEA Intermediate Season 18',
        'http://play.esea.net/index.php?s=league&d=standings&division_id=2431',
        'ESEA', 'http://i.imgur.com/KCZZVDH.jpg', 'http://i.imgur.com/cQ88n4A.png',
        ['twitch.tv/ESEA'], [1], 'SEASON', datetime.utcnow()),
]

def generate_events(t, db):
    for event in EVENTS:
        t.execute("""
            INSERT INTO events (name, website, league, logo, splash, streams, games, etype, start_date, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true);
        """, event)

MATCHES = [
    {
        "game": 1,
        "event": 1,
        "teams": [1, 5],
        "state": "OPEN",
        "itemstate": "OPEN",
        "meta": {
            "streams": ["http://twitch.tv/test1", "http://twitch.tv/test2"],
            "maps": ["de_nuke"]
        },
        "lock_date": ONE_WEEK_FUTURE,
        "match_date": ONE_WEEK_FUTURE,
        "public_date": datetime.utcnow()
    },
    {
        "game": 1,
        "event": 2,
        "state": "OPEN",
        "itemstate": "OPEN",
        "teams": [3, 4],
        "meta": {
            "note": "This is a test note!",
            "streams": ["http://mlg.tv/swag", "http://twitch.tv/esea"],
            "maps": ["de_nuke", "de_mirage", "de_dust2"]
        },
        "lock_date": ONE_WEEK_FUTURE,
        "match_date": ONE_WEEK_FUTURE,
        "public_date": datetime.utcnow()
    },
    {
        "game": 1,
        "event": 1,
        "state": "WAITING",
        "itemstate": "LOCKED",
        "teams": [5, 6],
        "meta": {
            "streams": ["http://mlg.tv/swag", "http://twitch.tv/esea"],
            "maps": ["de_facade", "de_mirage", "de_dust2"]
        },
        "lock_date": ONE_WEEK_PAST,
        "match_date": ONE_WEEK_PAST,
        "public_date": ONE_WEEK_PAST,
    }
]

MATCH_QUERY = """
INSERT INTO matches (event, state, itemstate, game, teams, meta, lock_date, match_date, public_date, active) VALUES
(%(event)s, %(state)s, %(itemstate)s, %(game)s, %(teams)s, %(meta)s, %(lock_date)s, %(match_date)s, %(public_date)s, true);
"""

def generate_matches(t, db):
    for match in MATCHES:
        match['meta'] = Json(match['meta'])
        t.execute(MATCH_QUERY, match)

betters = range(1, len(RANDOM_STEAMIDS))

BETS = [
    {
        "better": betters.pop(0),
        "match": 3,
        "team": random.choice([5, 6]),
        "value": random.randint(1, 40),
        "state": "CONFIRMED",
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
        q = BET_QUERY.format(", ".join([str(random.randint(1, 40000)) for i in range(4)]))
        t.execute(q, entry)


ITEM_TYPE_QUERY = """
INSERT INTO itemtypes (id, name) VALUES
(%(id)s, %(name)s);
"""

ITEM_QUERY = """
INSERT INTO items (id, type_id, class_id, instance_id, price, state) VALUES
(%(id)s, %(type)s, %(id)s, %(id)s, %(price)s, 'INTERNAL');
"""

def generate_items(t, db):
    types = range(1, 25000)

    for entry in types:
        t.execute(ITEM_TYPE_QUERY, {
            "id": entry,
            "name": "Test Item #%s" % entry
        })

    for id in range(50000):
        t.execute(ITEM_QUERY, {
            "id": id,
            "type": random.choice(types),
            "price": random.randint(100, 4000) / 100.0
        })


DATA_GENERATORS = [
    generate_bots,
    generate_users,
    generate_games,
    generate_teams,
    generate_events,
    generate_matches,
    generate_items,
    generate_bets
]

