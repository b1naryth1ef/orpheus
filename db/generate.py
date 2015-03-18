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
    ("c9", "Cloud9", "cloud9.png"),
    ("fnatic", "Fnatic", "fnatic.png"),
    ("HellRaisers", "HellRaisers", "hellraisers.png"),
    ("dignitas", "Team Dignitas", "dignitas.png"),
    ("nip", "Ninjas In Pajamas", "nip.png"),
    ("virtus.pro", "Virtus Pro", "virtuspro.png"),
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


ITEM_QUERY = """
INSERT INTO items (id, name, class_id, instance_id, price, state) VALUES
(%(id)s, %(name)s, %(id)s, %(id)s, %(price)s, 'INTERNAL');
"""

def generate_items(t, db):
    for id in range(50000):
        t.execute(ITEM_QUERY, {
            "id": id,
            "name": "Test Item #%s" % id,
            "price": random.randint(100, 4000) / 100.0
        })

BAN_QUERY = """
INSERT INTO bans (steamid, active, created_at, start_date, end_date, created_by, reason, description) VALUES
(%(steamid)s, %(active)s, %(created_at)s, %(start_date)s, %(end_date)s, %(created_by)s, %(reason)s, %(description)s);
"""

ban_reasons = [
        "Annoying individual",
        "Scammer",
        "Cheater",
        "Throws games for profit",
        "Unsavory individual",
        "Alt account",
        "I felt like banning this guy",
        "Really bad at CS",
        "Plays League of Legends",
        "All-around asshole and bad guy",
        "Gambling addict",
        "Do Not Unban",
        "Generic reason",
        "Another generic reason",
        "One more for good measure"
]

ban_descriptions = [
        "Attempted to scam me out of my knife",
        "Operates an underground network of game throwers",
        "Steel's alt account",
        "Cheated in a matchmaking game",
        "Some generic ban description",
        "Another generic ban description",
        "Some variety here",
        "Runs with scissors habitually",
        "Stole my bike"
]

def generate_bans(t, db):
    print "GENERATING BANS"
    num = 1000
    users = "SELECT * FROM users WHERE id >= 1 AND id <= " + str(num) + ";"
    t.execute(users)
    bans = [] 

    for record in t:
    
        banned = { 
                 "steamid": record[1],
                 "created_at": pg_utcnow(),
                 "start_date": pg_utcnow(),
                 "end_date": pg_utcnow(),  
                 "created_by": 30000, 
                 "active": bool(random.getrandbits(1)),
                 "reason": random.choice(ban_reasons), 
                 "description": random.choice(ban_descriptions)
        }

        bans.append(banned)

    for banned in bans:
        t.execute(BAN_QUERY, banned)

def pg_utcnow(): 
    import psycopg2
    return datetime.utcnow().replace(tzinfo=psycopg2.tz.FixedOffsetTimezone(offset=0, name=None))


DATA_GENERATORS = [
    generate_bots,
    generate_users,
    generate_games,
    generate_teams,
    generate_events,
    generate_matches,
    generate_items,
    generate_bets,
    generate_bans
]

