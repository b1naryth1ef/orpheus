from datetime import datetime
from database import Cursor

BOT_SPACE_QUERY = """
SELECT count(*) * 999 as c, sum(array_length(inventory, 1)) as s FROM bots WHERE status > 'NOAUTH'
"""

def get_bot_space():
    """
    Returns the amount of bot-slots used, and the amount avail
    """
    with Cursor() as c:
        b_cap = c.execute(BOT_SPACE_QUERY).fetchone()

        return b_cap.s or 0, b_cap.c or 0

