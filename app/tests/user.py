import unittest, json

from psycopg2 import IntegrityError
from flask import g

import emporium
from tests import FlaskTestCase
from helpers.user import create_user
from database import transaction

B1N_STEAM_ID = "76561198037632722"

class UserHelper(object):
    def get_user(self):
        with transaction() as t:
            t.execute("SELECT id FROM users WHERE steamid=%s", (B1N_STEAM_ID, ))
            return t.fetchone().id

class TestUsersUnit(unittest.TestCase, UserHelper):
    def setUp(self):
        # Cleanup  users
        with transaction() as t:
            t.execute("DELETE FROM users WHERE steamid=%s", (B1N_STEAM_ID, ))

    def test_create_user(self):
        uid = create_user(B1N_STEAM_ID)
        self.assertGreaterEqual(uid, 1)

        with transaction() as t:
            t.execute("SELECT count(*) as count FROM users")
            count = t.fetchone().count
            self.assertGreaterEqual(count, 1)

        self.assertRaises(IntegrityError, create_user, (B1N_STEAM_ID, ))

class TestUserIntegration(FlaskTestCase, UserHelper):
    def test_user_info_logged_out(self):
        rv = self.app.get("/auth/info")
        data = json.loads(rv.data)

        self.assertTrue(data['success'])
        self.assertFalse(data['authed'])

    def test_user_info_logged_in(self):
        rv = self.app.get("/auth/info", headers={"FAKE_USER": self.get_user()})
        data = json.loads(rv.data)

        self.assertTrue(data['success'])
        self.assertTrue(data['authed'])
        self.assertEqual(data['user']['steamid'], B1N_STEAM_ID)
        self.assertGreaterEqual(data['user']['id'], 1)

