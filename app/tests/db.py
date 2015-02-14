import unittest, json

from database import Cursor
from tests import UnitTest, IntegrationTest, TEST_STEAM_ID

class TestCursorUnit(UnitTest):
    def setUp(self):
        self.c = Cursor()

    def test_multiple_iteration(self):
        return
        count = self.c.execute("SELECT count(*) as c FROM users").fetchone().c
        results = self.c.execute("SELECT id FROM users").fetchall()

        self.assertEqual(len(results), count)

        # First Iteration
        c = 0
        for entry in results:
            c += 1

        self.assertEqual(c, count)

        # Second Iteration
        c = 0
        for entry in results:
            c += 1

        self.assertEqual(c, count)

