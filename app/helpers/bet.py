import time, json
from datetime import datetime

from database import Cursor, redis

from util import create_enum

BetState = create_enum('OFFERED', 'CONFIRMED', 'WON', 'LOST', 'CANCELLED')

CREATE_BET_SQL = """
INSERT INTO bets (better, match, team, items, value, state, created_at)
VALUES (%(user)s, %(match)s, %(team)s, %(items)s, %(value)s, %(state)s, %(created_at)s)
RETURNING id;
"""

LOCK_ITEM_SQL = """
UPDATE items SET price=%s WHERE id=%s
"""

def create_bet(user, match, team, items):
    with Cursor() as c:
        items_q = c.execute("""
            SELECT items.id as id, itemtypes.price as price, items.type_id FROM items
            JOIN itemtypes ON itemtypes.id=items.type_id
            WHERE items.id IN %s
        """, (tuple(items), )).fetchall(as_list=True)

        print len(items), len(items_q)
        print items, items_q

        # We need all dem results doh
        if not len(items) == len(items_q):
            raise Exception("Attempted betting invalid item")

        for item in items_q:
            c.execute(LOCK_ITEM_SQL, (item.price, item.id))

        data = {
            'user': user,
            'match': match,
            'team': team,
            'items': items,
            'state': BetState.OFFERED,
            'created_at': datetime.utcnow(),
            'value': sum(map(lambda i: i.price, items_q)),
        }

        id = c.execute(CREATE_BET_SQL, data).fetchone()

        redis.rpush("trade-queue", json.dumps({
            "time": time.time(),
            "type": "INTAKE",
            "id": id.id
        }))

    return id

