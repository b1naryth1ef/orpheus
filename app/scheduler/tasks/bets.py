from database import Cursor
from datetime import datetime
from dateutil.relativedelta import relativedelta

STUCK_BETS_QUERY = """
SELECT b.id, b.state, b.better, b.match, b.created_at, m.results_at FROM bets b
JOIN matches m ON m.id = b.match
WHERE b.state='offered' AND
    (b.created_at < %(date)s OR m.results_at < %(date)s)
"""

def run_find_stuck_bets():
    with Cursor() as c:
        stuck = c.execute(STUCK_BETS_QUERY, {
            "date": datetime.utcnow() - relativedelta(days=1),
        }).fetchall()

    print "There are %s stuck bets!" % len(stuck)
    # TODO: Send an email here?

