import json
from database import redis

class WebPush(object):
    def __init__(self, user=None):
        self.key = "ws:global" if not user else "ws:user:%s" % user

    def send(self, content):
        redis.publish(self.key, json.dumps(content))

