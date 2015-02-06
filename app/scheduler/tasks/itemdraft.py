import logging, traceback

from datetime import datetime

from database import Cursor
from util.itemdraft import pre_draft, run_draft
from util.uemail import Email

RUN_MATCH_DRAFT_QUERY = """
SELECT id, lock_date, match_date, results FROM matches
WHERE lock_date < %s AND active AND draft_started_at IS NULL
LIMIT 1
"""

log = logging.getLogger(__name__)

def run_item_drafts():
    """
    Finds matches that have just been locked (aka started being played)
    and run item drafts for them.
    """

    with Cursor() as c:
        entry = c.execute(RUN_MATCH_DRAFT_QUERY, (datetime.utcnow(), )).fetchone()

        if not entry:
            return

        log.info("Running entire draft process for match #%s", entry.id)

        # First thing we need to tell everyone we're working on this
        c.execute("UPDATE matches SET draft_started_at=%s WHERE id=%s", (datetime.utcnow(), entry.id))

        try:
            # Huge queries are good duh
            BETTERS = c.execute("""
                SELECT id, better, value, items, team FROM bets WHERE match=%s
            """, (entry.id, )).fetchall(as_list=True)

            # Calculate some basic stuff
            winning_team = entry.results.get("winner") if entry.results else -1
            total_value = sum(map(lambda i: i.value, BETTERS))
            winning_team_value = sum(map(lambda i: i.value if i.team == winning_team else 0, BETTERS))

            # Get our bodies ready for the draft code
            betters = [(item.id,
                ((total_value * 1.0) / winning_team_value) * item.value)
                for item in BETTERS if item.team == winning_team]
            skins = []

            # Lets just loop over more shit shall we
            for bet in BETTERS:
                # We can't give out returns
                if bet.team == winning_team:
                    continue

                skins += [(bet.id, item.item_id, item.item_meta.get("price")) for item in bet.items]

            # Pre-draft will insert the items we need
            log.info("Running predraft for match #%s" % entry.id)
            pre_draft(entry.id, winning_team, betters, skins)

            # Run-draft will actually draft items
            log.info("Running draft for match #%s" % entry.id)
            run_draft(entry.id, winning_team)
        except Exception as e:
            log.exception("Error during item draft run: ")
            e = Email()
            e.to_addrs = ["b1naryth1ef@gmail.com"]
            e.subject = "CSGOE Item Draft FAILED: #%s (%s)" % (entry.id, e)
            e.body = traceback.format_tb(e)
            e.send()

            with Cursor() as c:
                c.execute("UPDATE matches SET draft_started_at=NULL WHERE id=%s", (entry.id, ))
            raise
        else:
            with Cursor() as c:
                c.execute("UPDATE matches SET draft_finished_at=%s WHERE id=%s", (datetime.utcnow(), entry.id))

