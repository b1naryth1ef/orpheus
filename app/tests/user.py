import unittest, json

from psycopg2 import IntegrityError

import emporium
from tests import UnitTest, IntegrationTest, TEST_STEAM_ID
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

    def test_user_authed_route(self):
        data = self.r.get(self.url("/auth/ping"))

        self.assertNotIn('pong', data.content)
        self.assertEqual(data.status_code, 200)
