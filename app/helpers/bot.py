from datetime import datetime
from database import Cursor

from util import create_enum

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

def create_bot_item_transfer(*args, **kwargs):
    pass

def create_return_trade(*args, **kwargs):
    pass

