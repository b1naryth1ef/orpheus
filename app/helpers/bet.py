from datetime import datetime

from database import transaction, as_json, redis

class BetState(object):
    OFFERED = "offered"
    CONFIRMED = "confirmed"
    WON = "won"
    LOST = "lost"

    ORDER = [OFFERED, CONFIRMED, WON, LOST]


CREATE_BET_SQL = """
INSERT INTO bets (better, match, team, items, value)
VALUES (%(user)s, %(match)s, %(team)s, %(items), %(value)s, %(state)s);
"""

def create_bet(user, match, team, items):
    data = {
        user: user,
        match: match,
        team: team,
        items: map(lambda i: i.split("_"), items),
        state: BetState.OFFERED,
    }

    # TODO: calculate value from item cache
    data['value'] = 0

    with transaction() as t:
        t.execute(CREATE_BET_SQL, data)

        redis.rpush("trade-queue", json.dumps({
            "type": "INTAKE",
            "id": t.lastrowid
        }))

    return t.lastrowid

