import time, json, hashlib
from datetime import datetime

from database import Cursor, redis

from tasks.trades import push_trade

from util import create_enum
from util.errors import FortException
from helpers.trade import TradeType, TradeState

BetState = create_enum('NEW', 'OFFERED', 'CONFIRMED', 'WON', 'LOST', 'CANCELLED')

FIND_AVAIL_BOT_SQL = """
SELECT b.id FROM bots b
LEFT OUTER JOIN trades t ON t.bot_ref=b.id
WHERE (
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

def get_pin(id):
    """
    Computes a pin for a bet id. This simply computes a MD5 hash for the ID,
    and returns the last 12 digits.
    """
    m = hashlib.md5()
    m.update(str(id))
    return m.hexdigest()[:12]

def find_avail_bot(items_count):
    """
    Attempts to find a bot with `count` availible inventory slots. Will return
    the bot's id if found, or 0 if no availbile bots exist.
    """
    # Max size minus what we need to store
    size_expected = 999 - items_count

    with Cursor() as c:
        bots = c.execute("""
            SELECT id, array_length(inventory, 1) as ilen FROM bots WHERE status='USED'
            AND (array_length(inventory, 1) < %s) OR (inventory='{}')
        """, (size_expected, )).fetchall(as_list=True)

        # N + FUCKIN 1 BAAABY!!!!
        for bot in bots:
            extra = c.execute("""
                SELECT sum(array_length(items_in, 1)) as ex FROM trades
                WHERE bot_ref=%s AND state in ('NEW', 'IN-PROGRESS', 'OFFERED')
                AND items_in != '{}';
            """, (bot.id, )).fetchone().ex

            if (bot.ilen or 0) + (extra or 0) < size_expected:
                return bot.id
    return 0

LOCK_ITEM_SQL = "UPDATE items SET price=%s WHERE id=%s"

def create_bet(user, match, team, items):
    """
    Creates and queues a bot based on a user, match, team and a set of items
    the user wishes to place. Raises a `FortException` if the bet cannot be
    placed.
    """
    with Cursor() as c:
        items_q = c.execute("""
            SELECT id, price FROM items WHERE items.id IN %s
        """, (tuple(items), )).fetchall(as_list=True)

        # We need all dem results doh
        if not len(items) == len(items_q):
            raise FortException("Attempted betting invalid item")

        # Lock a price for all the items
        for item in items_q:
            c.execute(LOCK_ITEM_SQL, (item.price, item.id))

        # Create a new bet
        bet = c.insert("bets", {
            'better': user,
            'match': match,
            'team': team,
            'items': items,
            'state': BetState.NEW,
            'created_at': datetime.utcnow(),
            'value': sum(map(lambda i: i.price, items_q)),
        })

        # Find a bot that has inventory space
        bot = find_avail_bot(len(items))

        if not bot:
            raise FortException("Bot's are full, please try again later!")

        # Get the user's steamid and token for the trade
        user = c.execute("SELECT id, steamid, trade_token FROM users WHERE id=%s",
            (user, )).fetchone()

        # Create a new trade
        tid = c.insert("trades", {
            'state': TradeState.NEW,
            'ttype': TradeType.BET,
            'to_id': user.steamid,
            'token': user.trade_token,
            'message': 'CSGO Fort Bet. Match #%s. Pin: %s' % (match, get_pin(bet)),
            'items_in': items,
            'items_out': [],
            'created_at': datetime.utcnow(),
            'user_ref': user.id,
            'bet_ref': bet,
            'bot_ref': bot,
        })

        push_trade.queue(tid)

    return bet

