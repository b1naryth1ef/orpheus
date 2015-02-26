import unittest, os, requests, thread, json

from database import Cursor, redis

B1N_STEAM_ID = "76561198037632722"
TEST_STEAM_ID = "76561198031651584"

class TestWebsocketClient(object):
    def __init__(self, user=None):
        self.keys = ["ws:global"]

        if user:
            self.keys.append("ws:user:%s" % user)

        self.client = redis.pubsub()
        self.client.subscribe(self.keys)

    def get(self, timeout=5):
        for item in self.client.listen():
            if item['type'] == 'message':
                return json.loads(item['data'])

class UserHelper(object):
    session = None

    def as_user(self, uid, gid="normal"):
        self.r.headers.update({"FAKE_USER": uid})
        return uid

    def get_user(self, id=B1N_STEAM_ID):
        with Cursor() as c:
            return c.execute("SELECT id FROM users WHERE steamid=%s", (id, )).fetchone().id

class MatchHelper(object):
    def get_match(self):
        with Cursor() as c:
            return c.execute("SELECT id FROM matches LIMIT 1").fetchone().id

class MetaHelper(UserHelper, MatchHelper):
    pass

class UnitTest(unittest.TestCase, MetaHelper):
    pass

class IntegrationTest(unittest.TestCase, MetaHelper):
    URL = "http://localhost:8321"

    def url(self, suffix):
        return self.URL + suffix

    def setUp(self):
        self.r = requests.Session()

