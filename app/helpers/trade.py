import logging, json, hashlib

from database import Cursor, redis
from util import create_enum
from util.errors import FortException

log = logging.getLogger(__name__)

TradeState = create_enum('NEW', 'IN-PROGRESS', 'OFFERED', 'ACCEPTED', 'REJECTED', 'UNKNOWN')
TradeType = create_enum('BET', 'RETURNS', 'INTERNAL')

def queue_trade(bot_id, trade_id):
    raise Exception("Deprecated. Use tasks.trade.push_trade")

def get_trade_pin(id):
    """
    Computes a pin for a trade id. This simply computes a MD5 hash for the ID,
    and returns the last 6 digits.
    """
    m = hashlib.md5()
    m.update(str(id))
    return m.hexdigest()[:6]

NOTIFY_MSG = """
<p>You have a pending trade <a href="https://steamcommunity.com/tradeoffer/{trade.offerid}" target="_blank">click here</a>
to view it.</p>
Trade PIN: <span class="text-warning">{pin}</span><br />
</p>
"""

def get_trade_notify_content(tid):
    with Cursor() as c:
        trade = c.execute("""
            SELECT t.id, t.bot_ref, t.user_ref, t.offerid, b.profilename FROM trades t
            JOIN bots b ON b.id=t.bot_ref
            WHERE t.id=%s
        """, (tid, )).fetchone()

        if not trade:
            raise Exception("Failed to find trade for trade_notify, %s" % tid)

        return trade.user_ref, NOTIFY_MSG.format(trade=trade, pin=get_trade_pin(trade.id))

