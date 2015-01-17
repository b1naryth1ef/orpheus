import unittest

from psycopg2 import IntegrityError

from helpers.user import create_user
from database import transaction

B1N_STEAM_ID = "76561198037632722"

class TestUsersUnit(unittest.TestCase):
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
