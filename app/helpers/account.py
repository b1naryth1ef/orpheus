from datetime import datetime

from database import transaction, as_json, ValidationError

BOT_SPACE_QUERY = """
SELECT sum(array_length(inventory, 1)) AS used, count(*) AS count FROM accounts WHERE status > 'NOAUTH'
"""

def get_bot_space():
    """
    Returns the amount of bot-slots used, and the amount avail
    """
    with transaction() as t:
        t.execute(BOT_SPACE_QUERY)
        row = t.fetchone()

        print row, row.used, row.count
        return row.used, (row.count * 999) - row.used

