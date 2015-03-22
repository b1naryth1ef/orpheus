import json
from database import redis

class WebPush(object):
    def __init__(self, user=None):
        self.key = "ws:global" if not user else "ws:user:%s" % user

    def send(self, content):
        redis.publish(self.key, json.dumps(content))
        return self

    def create_hover(self, title, content):
        self.send({"type": "hover", "content": content, "title": title, "action": "create"})
        return self

    def clear_hover(self):
        self.send({"type": "hover", "action": "clear"})
        return self

