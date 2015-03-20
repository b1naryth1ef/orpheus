import logging, json

from database import redis
from util import create_enum
from util.errors import FortException

log = logging.getLogger(__name__)

TradeState = create_enum('NEW', 'IN-PROGRESS', 'OFFERED', 'ACCEPTED', 'REJECTED', 'UNKNOWN')
TradeType = create_enum('BET', 'RETURNS', 'INTERNAL')

def queue_trade(bot_id, trade_id):
    raise Exception("Deprecated. Use tasks.trade.push_trade")

