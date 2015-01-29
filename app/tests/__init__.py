import unittest, emporium, os, requests

from database import Cursor

B1N_STEAM_ID = "76561198037632722"
TEST_STEAM_ID = "76561198031651584"

class UserHelper(object):
    session = None

    def as_user(self, uid, gid="normal"):
        self.r.headers.update({"FAKE_USER": uid})

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
    URL = "http://localhost:5000"

    def url(self, suffix):
        return self.URL + suffix

    def setUp(self):
        self.r = requests.Session()

