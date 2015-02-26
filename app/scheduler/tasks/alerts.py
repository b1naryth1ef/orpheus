import json, time, traceback, logging

from util.email import Email

from fort import app
from database import Cursor, redis
from util.slack import SlackMessage

log = logging.getLogger(__name__)

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

        slack_color = 'danger' if level == AlertLevel.CRITICAL else 'warning'
        msg = SlackMessage("Check %s: %s (%s)" % (level, self.NAME.title(), ' '.join(sub_ctx or [])), color=slack_color)
        for field, value in msg_ctx.items():
            msg.add_custom_field(field, value)
        msg.send()

        e = Email()
        e.to_addrs = app.config.get("ALERT_EMAILS")
        e.subject = "CSGOE ALERT: %s %s (%s)" % (
            self.NAME,
            level,
            ', '.join(sub_ctx or [])
        )
        e.body = "\n".join(map(lambda i: "%s: %s" % i, msg_ctx.items()))
        e.send()

class TradeQueueSizeCheck(Check):
    NAME = "Trade Queue Size Check"
    THRESHOLD_WARNING = 100
    THRESHOLD_CRITICAL = 500

    def run(self):
        size = 0
        for queue in redis.keys("bot:*:tradeq"):
            size += int(redis.llen(queue) or 0)

        if size >= self.THRESHOLD_WARNING:
            level = AlertLevel.CRITICAL if (size >= self.THRESHOLD_CRITICAL) else AlertLevel.WARNING

            self.send_message(level, [size])

class PostgresDBCheck(Check):
    NAME = "Postgres DB Check"

    def run(self):
        with Cursor() as c:
            try:
                c.execute("SELECT 1337 AS v")
                raise Exception("Test exception")
                assert(c.fetchone().v == 1337)
            except Exception as e:
                self.send_message(AlertLevel.CRITICAL, [], {
                    "Exception:": traceback.format_exc()
                })

class RedisDBCheck(Check):
    NAME = "Redis DB Check"

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

