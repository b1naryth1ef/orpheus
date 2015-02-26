"""
This scheduled task was built to find possible fradulent situations with bets.
By tracking the players of teams, and getting a tree of their friends, we can
attempt to find bets that seem like malicious activity.
"""

from fort import steam
from database import Cursor

def get_all_friends(ids):
    """
    Returns an aggergated list of all friends a given steam-id has.
    """
    friends = set()

    for id in ids:
        friends = friends | set(steam.getFriendList(id))

    return friends

def check_match(mid):
    with Cursor() as c:
        teams = c.execute("SELECT teams FROM matches WHERE id=%s", (mid, )).fethcone().teams
        friends = get_all_friends(teams)

def run_fraud_check():
    pass
