import time, json
from datetime import datetime

from database import transaction, as_json, redis
from util.custom import SteamItem

class BetState(object):
    OFFERED = "offered"
    CONFIRMED = "confirmed"
    WON = "won"
    LOST = "lost"

    ORDER = [OFFERED, CONFIRMED, WON, LOST]


CREATE_BET_SQL = """
INSERT INTO bets (better, match, team, items, value, state)
VALUES (%(user)s, %(match)s, %(team)s, %(items)s, %(value)s, %(state)s)
RETURNING id;
"""

def create_bet(user, match, team, items):
    data = {
        'user': user,
        'match': match,
        'team': team,
        'items': map(lambda i: SteamItem(*i.split("_")), items),
        'state': BetState.OFFERED,
    }

    # TODO: calculate value from item cache
    data['value'] = 0

    with transaction() as t:
        t.execute(CREATE_BET_SQL, data)
        id = t.fetchone().id

        redis.rpush("trade-queue", json.dumps({
            "time": time.time(),
            "type": "INTAKE",
            "id": id
        }))

    return id

