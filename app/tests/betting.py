import unittest, json

from tests import UnitTest, IntegrationTest
from helpers.bet import create_bet

class TestBetsUnit(UnitTest):
    def test_create_bet(self):
        user = self.get_user()
        match = self.get_match()

        id = create_bet(user, match, 0, [])
        self.assertGreaterEqual(id, 1)

class TestBetsIntegration(IntegrationTest):
    def test_create_bet_invalid_match(self):
        self.as_user(self.get_user())
        data = self.r.post(self.url("/api/match/1337/bet"), params={
            "items": json.dumps(["0_0"]), "team": 0}).json()

        self.assertFalse(data['success'])

    def test_create_bet_invalid_team(self):
        self.as_user(self.get_user())
        data = self.r.post(self.url("/api/match/1/bet"), params={
            "items": json.dumps(["0_0"]), "team": 500}).json()

        self.assertFalse(data['success'])

    def test_create_bet_invalid_items(self):
        self.as_user(self.get_user())
        data = self.r.post(self.url("/api/match/1/bet"), params={
            "items": json.dumps([]), "team": 1}).json()

        self.assertFalse(data['success'])

    def test_create_bet(self):
        self.as_user(self.get_user())
        data = self.r.post(self.url("/api/match/1/bet"), params={
            "items": json.dumps(["0_0"]), "team": 1}).json()

        self.assertTrue(data['success'])

    def test_create_multiple_bets(self):
        self.as_user(self.get_user())
        data = self.r.post(self.url("/api/match/2/bet"), params={
            "items": json.dumps(["0_0"]), "team": 1}).json()
        self.assertTrue(data['success'])

        data = self.r.post(self.url("/api/match/2/bet"), params={
            "items": json.dumps(["0_0"]), "team": 1}).json()
        self.assertFalse(data['success'])

