import logging, json, time

from datetime import datetime
from dateutil import relativedelta

from database import Cursor, redis
from tasks import task

from tasks.bots import refresh_bot_inventory

from util import create_enum
from helpers.trade import TradeState, get_trade_notify_content
from util.push import WebPush
from util.steam import SteamAPI

log = logging.getLogger(__name__)

ETradeOfferState = create_enum("NULL", "INVALID", "ACTIVE", "ACCEPTED", "COUNTERED", "EXPIRED",
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

        # First, give a chance to any arbiter that has our specified bot loaded up
        if trade.bid and trade.status == "USED":
            # if redis.llen("tradeq:bot:%s" % trade.bid) or 0 > 25:
            #    raise Exception("Queue Full")

            redis.rpush("tradeq:bot:%s" % trade.bid, json.dumps(payload))
            time.sleep(5)

            if c.select("trades", "state", id=tid).fetchone().state != TradeState.NEW:
                log.debug("A bot handled the trade from the individual queue...")
                return

            # This will bite me in the ass later
            redis.delete("tradeq:bot:%s" % trade.bid)

#        if redis.llen("tradeq") or 0 > 50:
#            raise Exception("Queue Full")

        # Otherwise, let the hoard take it
        redis.rpush("tradeq", json.dumps(payload))

@task()
def update_trades():
    with Cursor() as c:
        trades = c.execute("""
            SELECT
                t.id, t.offerid, t.created_at, t.bet_ref, t.bot_ref, b.steamid, b.apikey,
                u.id as uid, m.id as mid
            FROM trades t
            JOIN bots b ON b.id=t.bot_ref
            JOIN users u ON u.id=t.user_ref
            LEFT OUTER JOIN bets bt ON bt.id=t.bet_ref
            LEFT OUTER JOIN matches m ON m.id=bt.match
            WHERE t.state='OFFERED'
        """).fetchall(as_list=True)

        for trade in trades:
            steam = SteamAPI(trade.apikey)
            offer = steam.getTradeOffer(trade.offerid)

            if trade.created_at < datetime.utcnow() - relativedelta.relativedelta(minutes=5):
                log.info("Canceling trade %s, expired", trade.id)
                c.update("trades", trade.id, state='REJECTED')

                if trade.bet_ref:
                    c.update("bets", trade.bet_ref, state='CANCELLED')
                    WebPush(trade.uid).clear_hover().send({"type": "refresh-match", "id": trade.mid})

                steam.cancelTradeOffer(trade.offerid)
                continue

            state = offer['trade_offer_state']
            log.info('Trade #%s state: %s', trade.id, state)
            if state == ETradeOfferState.INVALID or state > ETradeOfferState.ACCEPTED:
                log.info("Canceling trade %s, state", trade.id)
                steam.cancelTradeOffer(trade.offerid)
                c.update("trades", trade.id, state='REJECTED')

                if trade.bet_ref:
                    c.update("bets", trade.bet_ref, state='CANCELLED')
                    WebPush(trade.uid).clear_hover().send({"type": "refresh-match", "id": trade.mid})
            elif state == ETradeOfferState.ACCEPTED:
                log.info("Updating state for trade %s, accepted", trade.id)
                c.update("trades", trade.id, state='ACCEPTED')

                refresh_bot_inventory.queue(trade.bot_ref, trade.steamid)
                if trade.bet_ref:
                    c.update("bets", trade.bet_ref, state='CONFIRMED')
                    WebPush(trade.uid).clear_hover().send({"type": "refresh-match", "id": trade.mid})

@task()
def trade_notify(tid):
    uid, content = get_trade_notify_content(tid)
    WebPush(uid).clear_hover()
    time.sleep(1)
    WebPush(uid).create_hover("Pending Trade Offer", content)

