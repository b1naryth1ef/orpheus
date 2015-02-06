import json, time, traceback, logging

from util.email import Email

from database import Cursor, redis

log = logging.getLogger(__name__)

# TODO: move to config
ALERT_EMAILS = ["b1naryth1ef@gmail.com"]

class AlertLevel(object):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class Check(object):
    NAME = "Generic Check"

    def run(self):
        raise NotImplementedError("Check subclass %s does not implement `run()`" % (
            self.__class__.__name__))

    def send_message(self, level, sub_ctx=None, msg_ctx=None):
        log.warning("Sending alert %s @ lvl %s" % (self.NAME, level))
        e = Email()
        e.to_addrs = ALERT_EMAILS
        e.subject = "CSGOE ALERT: %s %s (%s)" % (
            self.NAME,
            level,
            ', '.join(sub_ctx or [])
        )
        e.body = "\n".join(map(lambda i: "%s: %s" % i, msg_ctx.items()))
        e.send()

class TradeQueueSizeCheck(Check):
    THRESHOLD_WARNING = 100
    THRESHOLD_CRITICAL = 500

    def run(self):
        size = int(redis.llen("trade-queue") or 0)

        if size >= self.THRESHOLD_WARNING:
            level = AlertLevel.CRITICAL if (size >= self.THRESHOLD_CRITICAL) else AlertLevel.WARNING
            queue = redis.lrange("trade-queue", 0, -1)

            self.send_message(level, [size], {
                "Bets in Queue": ', '.join(queue),
                "Queued Since (s)": time.time() - json.loads(queue[-1])["time"]
            })

class PostgresDBCheck(Check):
    def run(self):
        with Cursor() as c:
            try:
                c.execute("SELECT 1337 AS v")
                assert(c.fetchone().v == 1337)
            except Exception as e:
                self.send_message(AlertLevel.CRITICAL, [], {
                    "Exception:": traceback.format_exc()
                })

class RedisDBCheck(Check):
    def run(self):
        try:
            redis.ping()
        except Exception as e:
            self.send_message(AlertLevel.CRITICAL, [], {
                "Exception:": traceback.format_exc()
            })


CHECKS = [TradeQueueSizeCheck(), PostgresDBCheck(), RedisDBCheck()]

def run_alert_checks():
    for check in CHECKS:
        try:
            check.run()
        except:
            log.exception("Failed to run check %s" % check.__class__.__name__)

