import logging, json
from datetime import datetime

from emporium import steam
from database import Cursor, redis
from util import create_enum

log = logging.getLogger(__name__)

TradeState = create_enum('NEW', 'IN-PROGRESS', 'OFFERED', 'ACCEPTED', 'REJECTED', 'UNKNOWN')
TradeType = create_enum('BET', 'RETURNS', 'INTERNAL')

def queue_trade(bot_id, trade_id):
    queue_key = "bot:%s:tradeq" % bot_id

    if redis.llen(queue_key) > 32:
        raise Exception("Bot #%s trade queue is full" % bot_id)

    redis.rpush(queue_key, json.dumps({'type': 'trade', 'id': trade_id}))

