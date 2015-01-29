import unittest, json, random, time

from tests import UnitTest, IntegrationTest
from helpers.bet import create_bet
from util.itemdraft import create_tables, pre_draft, run_draft

class ItemDraftUnitTest(UnitTest):
    def generate_values(self, min_value, max_value, count):
        min_value = min_value * 100
        max_value = max_value * 100
        return map(lambda _: random.randint(min_value, max_value) / 100.0, range(count))

    def to_tupleset(self, values):
        return map(lambda i: (i[0], i[1]), enumerate(values))

    def setUp(self):
        create_tables()

    def test_small_draft(self):
        simple_itemset = self.to_tupleset(self.generate_values(0.05, 20, 5000))
        simple_betset = self.to_tupleset(self.generate_values(0.10, 80, 1000))

        match_id = team_id = 256 ** 4
        pre_draft(match_id, team_id, simple_betset, simple_itemset)
        run_draft(match_id, team_id)

