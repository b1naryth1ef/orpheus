from database import transaction
from datetime import datetime

RUN_MATCH_DRAFT_QUERY = """
SELECT id, lock_date, match_date FROM matches
WHERE lock_date < %s AND active;
"""

def run_item_drafts():
    """
    Finds matches that have just been locked (aka started being played)
    and run item drafts for them.

    TODO: run this on a background box eventually
    """

    with transaction() as t:
        t.execute(RUN_MATCH_DRAFT_QUERY, (datetime.utcnow(), ))
        results = t.fetchall()

        if not len(results):
            return

        print "Found %s matches that can have item drafts ran!" % len(results)

        for entry in results:
            # TODO: update match.draft_started_at
            # TODO: queue draft shit
            # TODO: update match.draft_finished_at
            # TODO: run some sanity checks
            # yay :D


USE_MATCH_QUERY = """
SELECT id, results, items_at, results_at FROM matches WHERE results_at IS NOT NULL
AND items_at < %s AND active;
"""

def use_item_drafts():
    """
    Finds matches that's results have been entered, and have past the
    item lock date.
    """

    with transaction() as t:
        t.execute(USE_MATCH_QUERY, (datetime.utcnow(), ))

        results = t.fetchall()

        if not len(results):
            return

        print "Found %s matches that can have items distributed" % len(results)

        # TODO: run last checks here! We're soooo fucked if the draft is wrong and it hits here!

        for entry in results:
            # TODO: query emporium_draft DB for items
            # TODO: update items in db
            # TODO: update bets table with winnings

        # TODO: dump emporium_draft DB for this match to a csv and store it somewhere

