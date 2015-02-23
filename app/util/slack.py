import json, logging
from slacker import Slacker

from emporium import app

log = logging.getLogger(__name__)
slack = Slacker('xoxb-3809520008-UCTKTT9r8AKOLUYXHhsk5jER')

def slack_message(content, color=None, fields=None, username=None, channel="#auto"):
    if app.config.get("ENV") != "PROD":
        log.debug("Would send slack message: %s, %s, %s, %s" % (content, color, fields, username))
        return

    slack.chat.post_message(channel, "",
        username=username or 'empburt',
        attachments=json.dumps([{
            "fallback": content,
            "text": content,
            "color": color,
            "fields": [{
                "title": item[0],
                "value": str(item[1]),
                "short": len(str(item[1])) < 64
            } for item in fields.items()]
        }]))

