from datetime import datetime
from database import Cursor

BOT_SPACE_QUERY = """
SELECT sum(array_length(inventory, 1)) AS used, count(*) AS count FROM accounts WHERE status > 'NOAUTH'
"""

def get_bot_space():
    """
    Returns the amount of bot-slots used, and the amount avail
    """
    with Cursor() as c:
        row = c.execute(BOT_SPACE_QUERY).fetchone()
        return row.used, (row.count * 999) - row.used

