import time, json
from datetime import datetime

from database import Cursor, redis
from util.custom import SteamItem

class BetState(object):
    OFFERED = "offered"
    CONFIRMED = "confirmed"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"

    ORDER = [OFFERED, CONFIRMED, WON, LOST, CANCELLED]


CREATE_BET_SQL = """
INSERT INTO bets (better, match, team, items, value, state, created_at)
VALUES (%(user)s, %(match)s, %(team)s, %(items)s, %(value)s, %(state)s, %(created_at)s)
RETURNING id;
"""

def create_bet(user, match, team, items):
    data = {
        'user': user,
        'match': match,
        'team': team,
        'items': map(lambda i: SteamItem(i.id, None, None, {
            "price": float(i.price)
        }), items),
        'state': BetState.OFFERED,
        'created_at': datetime.utcnow(),
    }

    data['value'] = sum(map(lambda i: i.price, items))

    with Cursor() as c:
        id = c.execute(CREATE_BET_SQL, data).fetchone()

        redis.rpush("trade-queue", json.dumps({
            "time": time.time(),
            "type": "INTAKE",
            "id": id
        }))

    return id

