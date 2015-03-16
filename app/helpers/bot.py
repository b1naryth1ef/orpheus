from datetime import datetime
from database import Cursor

from util import create_enum
from tasks.trades import push_trade

BotStatus = create_enum('NEW', 'COOLDOWN', 'AVAIL', 'USED', 'INVALID')

BOT_SPACE_QUERY = """
SELECT count(*) * 999 as c, sum(array_length(inventory, 1)) as s
FROM bots WHERE status IN ('%s', '%s')
""" % (BotStatus.AVAIL, BotStatus.USED)

def get_bot_space():
    """
    Returns the amount of bot-slots used, and the amount avail
    """
    with Cursor() as c:
        b_cap = c.execute(BOT_SPACE_QUERY).fetchone()

        return b_cap.s or 0, b_cap.c or 0

def create_bot_item_transfer(from_bot, to_bot, items):
    pass

def create_return_trade(bot_id, user_id, items):
    with Cursor() as c:
        u = c.execute("SELECT trade_token, steamid FROM users WHERE id=%s", (user_id, )).fetchone()

        tid = c.insert("trades", {
            "token": u.trade_token,
            "state": "NEW",
            "ttype": "RETURNS",
            "to_id": u.steamid,
            "message": "CSGO Fort Bet Returns",
            "items_out": items,
            "created_at": datetime.utcnow(),
            "bot_ref": bot_id,
            "user_ref": user_id
        })

        push_trade(tid)
        return tid

