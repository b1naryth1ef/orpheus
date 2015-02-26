import unittest, json

from psycopg2 import IntegrityError

from tests import UnitTest, IntegrationTest, TEST_STEAM_ID, TestWebsocketClient
from helpers.user import create_user
from database import Cursor

FAKE_STEAM_ID = "76561198031554200"

class TestUsersUnit(UnitTest):
    def test_create_user(self):
        uid = create_user(FAKE_STEAM_ID)
        self.assertGreaterEqual(uid, 1)

        with Cursor() as c:
            count = c.count("users")
            self.assertGreaterEqual(count, 1)

        self.assertRaises(IntegrityError, create_user, (FAKE_STEAM_ID, ))

class TestUserIntegration(IntegrationTest):
    def test_user_info_logged_out(self):
        data = self.r.get(self.url("/auth/info")).json()

        self.assertTrue(data['success'])
        self.assertFalse(data['authed'])

    def test_user_info_logged_in(self):
        self.as_user(self.get_user(TEST_STEAM_ID))

        data = self.r.get(self.url("/auth/info")).json()

        self.assertTrue(data['success'])
        self.assertTrue(data['authed'])
        self.assertEqual(data['user']['steamid'], TEST_STEAM_ID)
        self.assertGreaterEqual(data['user']['id'], 1)

    def test_user_unauthed_inventory(self):
        data = self.r.get(self.url("/api/user/%s/inventory" % self.get_user(TEST_STEAM_ID)))
        self.assertNotEqual(data.status_code, 200)
        self.assertFalse(data.json()['success'])

    def test_user_inventory(self):
        id = self.as_user(self.get_user(TEST_STEAM_ID))
        cli = TestWebsocketClient(id)

        data = self.r.get(self.url("/api/user/%s/inventory" % id)).json()
        ws_data = cli.get()

        self.assertTrue(ws_data['success'])
        self.assertGreaterEqual(len(ws_data['inventory']), 1)

    def test_user_authed_route(self):
        data = self.r.get(self.url("/auth/ping"))

        self.assertNotIn('pong', data.content)
        self.assertEqual(data.status_code, 200)

