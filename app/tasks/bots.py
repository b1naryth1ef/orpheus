import json, logging

from dateutil.relativedelta import relativedelta
from datetime import datetime

from database import redis, Cursor
from tasks import task

log = logging.getLogger(__name__)

@task
def check_single_queue(qid):
    entry = redis.lrange(qid, -1, -1)
    if not len(entry):
        return

    entry = entry[0]
    data = json.loads(entry)

    with Cursor() as c:
        trade = c.execute("SELECT state, created_at FROM trades WHERE id=%s", (data['id'], )).fetchone()

        if not trade:
            log.warning("Trade %s doesn't exist. Wat?" % data['id'])
            return

        five_minutes_ago = datetime.utcnow() - relativedelta(minutes=5)
        if trade.created_at < five_minutes_ago:
            log.warning("Queue %s is backed up. Flushing..." % qid)

            # We'll let these trades naturally die
            # TODO: would be qewl to requeue these
            redis.delete(qid)
            return

@task
def run_find_stuck_trades():
    map(check_single_queue, redis.keys("bot:*:tradeq"))

