import unittest, json

from tests import UnitTest, IntegrationTest

class TestUserIntegration(IntegrationTest):
    def test_match_list(self):
        data = self.r.get(self.url("/api/match/list")).json()

        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['matches']), 1)

    def test_single_match(self):
        data = self.r.get(self.url("/api/match/1/info")).json()

        self.assertTrue(data['success'])
        self.assertNotEqual(data['match'], {})

