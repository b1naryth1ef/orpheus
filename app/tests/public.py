import unittest, json

from tests import FlaskTestCase


class TestUserIntegration(FlaskTestCase):
    def test_match_list(self):
        rv = self.app.get("/api/match/list")
        data = json.loads(rv.data)

        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['matches']), 1)

    def test_single_match(self):
        rv = self.app.get("/api/match/1/info")
        data = json.loads(rv.data)

        self.assertTrue(data['success'])
        self.assertNotEqual(data['match'], {})

