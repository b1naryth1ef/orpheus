import json, logging
from slacker import Slacker

from emporium import app

log = logging.getLogger(__name__)
slack = Slacker('xoxb-3809520008-UCTKTT9r8AKOLUYXHhsk5jER')

class SlackMessage(object):
    def __init__(self, content, color=None, username="empburt", channel="#ops"):
        self.text = content
        self.color = color
        self.username = username
        self.channel = channel

        self.fallback = None
        self.pretext = None
        self.author_name = None
        self.author_link = None
        self.author_icon = None
        self.title = None
        self.title_link = None
        self.image_url = None

        self.fields = {}

    def add_custom_field(self, title, value, short=None):
        short = len(str(value)) < 64 if short is None else short

        self.fields.append({
            "title": title,
            "value": value,
            "short": short
        })

    def payload(self):
        return (self.channel, ""), {
            'username': self.username,
            'attachments': json.dumps({
                "fallback": self.fallback,
                "color": self.color,
                "pretext": self.pretext,
                "author_name": self.author_name,
                "author_link": self.author_link,
                "author_icon": self.author_icon,
                "title": self.title,
                "title_link": self.title_link,
                "text": self.text,
                "fields": self.fields,
                "image_url": self.image_url
            })}

    def send_async(self):
        from util.queue import JobQueue
        args, kwargs = self.payload()
        return JobQueue("slack_msg").fire({"args": args, "kwargs": kwargs})

    def send(self):
        if app.config.get("ENV") != "PROD":
            log.debug("Would send slack message: %s, %s, %s, %s" %
                (content, color, fields, username))
            return
        self.send_raw(*self.payload())

    @staticmethod
    def send_raw(args, kwargs):
        return self.chat.post_message(*args, **kwargs)
