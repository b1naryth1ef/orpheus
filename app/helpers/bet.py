import time, json
from datetime import datetime

from database import Cursor, redis, create_insert_query

from util import create_enum
from util.errors import EmporiumException
from helpers.trade import queue_trade, TradeType, TradeState

BetState = create_enum('NEW', 'OFFERED', 'CONFIRMED', 'WON', 'LOST', 'CANCELLED')

CREATE_BET_SQL = create_insert_query("bets", "better", "match", "team", "items",
    "value", "state", "created_at")

CREATE_TRADE_SQL = create_insert_query("trades",
    "state", "ttype", "to_id", "message", "items_in", "items_out", "created_at",
    "user_ref", "bet_ref", "bot_ref", "token")

FIND_AVAIL_BOT_SQL = """
SELECT b.id FROM bots b
LEFT OUTER JOIN trades t ON t.bot_ref=b.id
WHERE b.status='USED' AND (
  (
    (t.state='NEW' OR t.state='IN-PROGRESS' OR t.state='OFFERED')
    AND array_length(t.items_in, 1) > 0
    AND (array_length(b.inventory, 1) + array_length(t.items_in, 1)) < %s
    OR b.inventory='{}'
  ) OR (
    t IS NULL
    AND (array_length(b.inventory, 1) < %s) OR b.inventory='{}'
  )
)
LIMIT 1;
"""

LOCK_ITEM_SQL = "UPDATE items SET price=%s WHERE id=%s"

def find_avail_bot(items_count):
    # Max size minus what we need to store
    size_expected = 999 - items_count

    with Cursor() as c:
        bot = c.execute(FIND_AVAIL_BOT_SQL, (size_expected, size_expected)).fetchone()

    return bot.id if bot else 0

def create_bet(user, match, team, items):
    with Cursor(transaction=True) as c:
        items_q = c.execute("""
            SELECT items.id as id, itemtypes.price as price, items.type_id FROM items
            JOIN itemtypes ON itemtypes.id=items.type_id
            WHERE items.id IN %s
        """, (tuple(items), )).fetchall(as_list=True)

        # We need all dem results doh
        if not len(items) == len(items_q):
            raise EmporiumException("Attempted betting invalid item")

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

        # Find a bot that has inventory space
        bot = find_avail_bot(len(items))

        if not bot:
            raise EmporiumException("No bot space availible")

        # Get the user's steamid and token for the trade
        user = c.execute("SELECT id, steamid, trade_token FROM users WHERE id=%s", (user, )).fetchone()

        # Create a new trade
        tid = c.execute(CREATE_TRADE_SQL, {
            'state': TradeState.NEW,
            'ttype': TradeType.BET,
            'to_id': user.steamid,
            'token': user.trade_token,
            'message': 'I should do this...',
            'items_in': items,
            'items_out': [],
            'created_at': datetime.utcnow(),
            'user_ref': user.id,
            'bet_ref': bid.id,
            'bot_ref': bot,
        }).fetchone()

        queue_trade(bot, tid.id)

    return bid.id

