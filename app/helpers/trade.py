import logging, json, hashlib

from database import redis
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
    and returns the last 12 digits.
    """
    m = hashlib.md5()
    m.update(str(id))
    return m.hexdigest()[:12]

