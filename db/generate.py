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
    ("clg", "Counter Logic Gaming", "counterLogicGaming.png"),
    ("CPH", "Copenhagen Wolves", "CPHWolves.png"),
    ("eLv", "eLevate", "eLevate.png"),
    ("FSid3", "Flipsid3", "flipsid3.png"),
    ("G2", "Gamers2", "gamers2.png"),
    ("LGB", "LGB eSports", "lgb.png"),
    ("LG", "Luminosity Gaming", "luminosityGaming.png"),
    ("mouz", "mousesports", "mousesports.png"),
    ("Na\`Vi", "Natus Vincere", "navi.jpg"),
    ("PENTA", "PENTA Sports", "penta.png"),
    ("TeamPro", "Team Property", "property.png"),
    ("SKDC", "SapphireKelownaDotCom", "skdc.jpg"),
    ("Liquid\`", "Team Liquid", "teamLiquid.png"),
    ("Titan", "Titan", "titan.png"),
    ("TSM", "Team Solo Mid", "tsm.jpg")
]

def generate_teams(t, db):
    for team in TEAMS:
        t.execute("INSERT INTO teams (tag, name, logo) VALUES (%s, %s, %s)", team)

EVENTS = [
    ('ESEA Invite Season 18',
        'http://play.esea.net/index.php?s=league&d=standings&division_id=2428',
        'ESEA', 'esea_splash.png', 'esea_logo.png',
        ['twitch.tv/ESEA'], [1], 'SEASON', datetime.utcnow()),
    ('ESEA Premier Season 18',
        'http://play.esea.net/index.php?s=league&d=standings&division_id=2429',
        'ESEA', 'esea_splash.png', 'esea_logo.png',
        ['twitch.tv/ESEA'], [1], 'SEASON', datetime.utcnow()),
    ('ESEA Main Season 18',
        'http://play.esea.net/index.php?s=league&d=standings&division_id=2430',
        'ESEA', 'esea_splash.png', 'esea_logo.png',
        ['twitch.tv/ESEA'], [1], 'SEASON', datetime.utcnow()),
    ('ESEA Intermediate Season 18',
        'http://play.esea.net/index.php?s=league&d=standings&division_id=2431',
        'ESEA', 'esea_splash.png', 'esea_logo.png',
        ['twitch.tv/ESEA'], [1], 'SEASON', datetime.utcnow()),
]

def generate_events(t, db):
    for event in EVENTS:
        t.execute("""
            INSERT INTO events (name, website, league, logo, splash, streams, games, etype, start_date, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true);
        """, event)

MATCH_QUERY = """
INSERT INTO matches (event, state, itemstate, game, teams, meta, results, match_date, public_date, active) VALUES
(%(event)s, %(state)s, %(itemstate)s, %(game)s, %(teams)s, %(meta)s, %(results)s, %(match_date)s, %(public_date)s, true);
"""
NUM_MATCHES = 750
NUM_MATCHES_PER_DAY = 4
MATCH_HAPPENED_PRB = 0.75

def generate_matches(t, db):
    match_date_accumulator = datetime.utcnow() + relativedelta(weeks=(-1 * (MATCH_HAPPENED_PRB * NUM_MATCHES) / (NUM_MATCHES_PER_DAY * 7 )))
    matches_today = 0; 
    match_date_accumulator = match_date_accumulator.replace(hour=1, minute=0) 
    for i in range (0, NUM_MATCHES):
        t1 = random.randrange(1, len(TEAMS))
        t2 = random.randrange(1, len(TEAMS))
        while t1 == t2:
            t2 = random.randrange(1, len(TEAMS))
        
        match_happened = random.random() < MATCH_HAPPENED_PRB
        
        match_date = ONE_WEEK_FUTURE
        public_date = datetime.utcnow()
        state = "OPEN"
        item_state="OPEN"
        results = {}
        if(match_happened):
            state = "COMPLETED"
            item_state = "DISTRIBUTED"
            match_date = match_date_accumulator
            public_date = match_date_accumulator + relativedelta(weeks=-1)
            matches_today = matches_today + 1
            match_date_accumulator = match_date_accumulator + relativedelta(minutes=3)
            if matches_today >= NUM_MATCHES_PER_DAY:
                if random.random() < 0.5 + 0.25 * (matches_today - NUM_MATCHES_PER_DAY):
                   matches_today = 0
                   match_date_accumulator = match_date_accumulator + relativedelta(days=1)
            results = {
                "winner": random.choice([t1, t2])
                    }
            #result['winner'] = Json(result['winner'])
        match = {
            "game": 1,
            "event": random.randrange(1, len(EVENTS)),
            "state": state,
            "itemstate": item_state,
            "teams": [t1, t2],
            "meta": {
                "streams": ["http://twitch.tv/esea"],
                "maps": ["de_nuke", "de_mirage", "de_dust2"]
            },
            "results": results,
            "match_date": match_date,
            "public_date": public_date
        }
        match['meta'] = Json(match['meta'])
        match['results']=Json(match['results'])
        t.execute(MATCH_QUERY, match);

BET_QUERY = """
INSERT INTO bets (better, match, team, value, items, state, created_at) VALUES
(%(better)s, %(match)s, %(team)s, %(value)s, ARRAY[{}], %(state)s, %(created_at)s);
"""
NUM_BETTERS = 100

# TODO
def generate_bets(t, db):
    """
    for index, entry in enumerate(BETS):
        if index % 10000 == 0:
            print "    Bet #%s" % index
            db.commit()
        q = BET_QUERY.format(", ".join([str(random.randint(1, 40000)) for i in range(4)]))
        t.execute(q, entry)
    """
    t.execute("SELECT * FROM matches")
    for record in t.fetchall():
        for better in range (1, NUM_BETTERS):
            q = BET_QUERY.format(", ".join([str(random.randint(1, 40000)) for i in range(4)]))
            entry = {
                "better": better,
                "match": record[0],
                "team": random.choice([record[5][0], record[5][1]]),
                "value": random.randint(1, 40),
                "state": "CONFIRMED",
                "created_at": datetime.utcnow(),
            }

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
    generate_games,
    generate_teams,
    generate_events,
    generate_matches,
    generate_users,
    generate_items,
    generate_bets,
    generate_bans
]

