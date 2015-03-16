import logging, json, time

from datetime import datetime
from dateutil import relativedelta

from database import Cursor, redis
from tasks import task

from util.steam import SteamAPI
from util import create_enum

log = logging.getLogger(__name__)

ETradeOfferState = create_enum("INVALID", "ACTIVE", "ACCEPTED", "COUNTERED", "EXPIRED",
    "CANCELED", "DECLINED", "INVALID", "EMAIL_CANCELLED")

@task()
def push_trade(tid):
    with Cursor() as c:
        trade = c.execute("""
            SELECT t.id as tid, t.items_in, t.items_out, b.id as bid, b.status
            FROM trades t LEFT JOIN bots b ON b.id=t.bot_ref
            WHERE t.id=%s
            """, (tid, )).fetchone()

        if not trade:
            raise Exception("push_trade failed, invalid trade id %s" % tid)

        payload = {
            "type": "trade",
            "id": trade.tid,
            "in": len(trade.items_in or []),
            "out": len(trade.items_out or []),
            "bot": trade.bid or 0
        }

        # Set a key to make this transactional
        redis.set("trade:%s" % trade.tid, 1)

        # First, give a chance to any arbiter that has our specified bot loaded up
        if trade.bid and trade.status == "USED":
            redis.publish("tradeq:bot:%s" % trade.bid, json.dumps(payload))
            time.sleep(3)

            # Let's see if someone managed to grab it
            if not redis.exists("trade:%s"):
                return

        # Otherwise, let the hoard take it
        redis.publish("tradeq", json.dumps(payload))

@task()
def update_trades():
    with Cursor() as c:
        trades = c.execute("""
            SELECT t.id, t.offerid, t.created_at, b.apikey FROM trades t
            JOIN bots b ON b.id=t.bot_ref
            WHERE state='OFFERED'
        """).fetchall(as_list=True)

        for trade in trades:
            steam = SteamAPI(trade.apikey)
            offer = steam.getTradeOffer(trade.offerid)

            if trade.created_at > datetime.now() - relativedelta.relativedelta(minutes=5):
                log.info("Canceling trade %s, expired", trade.id)
                steam.cancelTradeOffer(trade.offerid)
                c.update("trades", trade.id, state='REJECTED')
                continue

            state = offer['trade_offer_state']
            if state == ETradeOfferState.INVALID or state > ETradeOfferState.ACCEPTED:
                log.info("Canceling trade %s, state", trade.id)
                steam.cancelTradeOffer(trade.offerid)
                c.update("trades", trade.id, state='REJECTED')
            elif state == ETradeOfferState.ACCEPTED:
                log.info("Updating state for trade %s, accepted", trade.id)
                c.update("trades", trade.id, state='ACCEPTED')
