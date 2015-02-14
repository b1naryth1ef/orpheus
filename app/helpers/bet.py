import time, json
from datetime import datetime

from database import Cursor, redis, create_insert_query

from util import create_enum
from helpers.trade import TradeType, TradeState

BetState = create_enum('NEW', 'OFFERED', 'CONFIRMED', 'WON', 'LOST', 'CANCELLED')

CREATE_BET_SQL = create_insert_query("bets", "better", "match", "team", "items", "value", "state", "created_at")
CREATE_TRADE_SQL = create_insert_query("trades",
    "state", "ttype", "to_id", "message", "items_in", "items_out", "created_at", "user_ref", "bet_ref")
LOCK_ITEM_SQL = "UPDATE items SET price=%s WHERE id=%s"

def create_bet(user, match, team, items):
    with Cursor(transaction=True) as c:
        items_q = c.execute("""
            SELECT items.id as id, itemtypes.price as price, items.type_id FROM items
            JOIN itemtypes ON itemtypes.id=items.type_id
            WHERE items.id IN %s
        """, (tuple(items), )).fetchall(as_list=True)

        # We need all dem results doh
        if not len(items) == len(items_q):
            raise Exception("Attempted betting invalid item")

        # Lock a price for all the items
        for item in items_q:
            c.execute(LOCK_ITEM_SQL, (item.price, item.id))

        # Create a new bet
        bid = c.execute(CREATE_BET_SQL, {
            'better': user,
            'match': match,
            'team': team,
            'items': items,
            'state': BetState.NEW,
            'created_at': datetime.utcnow(),
            'value': sum(map(lambda i: i.price, items_q)),
        }).fetchone()

        # Get the user's steamid for the trade
        user = c.execute("SELECT id, steamid FROM users WHERE id=%s", (user, )).fetchone()

        # Create a new trade
        tid = c.execute(CREATE_TRADE_SQL, {
            'state': TradeState.NEW,
            'ttype': TradeType.BET,
            'to_id': user.steamid,
            'message': 'I should do this...',
            'items_in': items,
            'items_out': [],
            'created_at': datetime.utcnow(),
            'user_ref': user.id,
            'bet_ref': bid.id
        }).fetchone()

        # Finally, we queue the bet to a bot
        redis.rpush("trade-queue", json.dumps({"id": tid.id}))

    return bid.id

