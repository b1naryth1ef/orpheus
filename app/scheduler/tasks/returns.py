import logging

from database import Cursor

log = logging.getLogger(__name__)

FIND_MATCH_FOR_APPLY = """
SELECT m.id as mid, dr.id as drid FROM matches m
JOIN item_drafts dr ON (
    dr.match=m.id AND dr.team=(m.results->'winner')::text::int)
WHERE m.state='RESULT' AND m.itemstate='LOCKED' AND dr.state='COMPLETED'
LIMIT 1
"""

def distribute_returns():
    pass

def apply_draft_items():
    dc = Cursor("fort_draft")

    with Cursor() as c:
        match = c.execute(FIND_MATCH_FOR_APPLY).fetchone()

        if not match:
            return

        # Take out our lock
        c.execute("UPDATE item_drafts SET state='USED' WHERE id=%s", (match.drid, ))

        # TODO: create checks to make sure its bueno
        items = dc.execute("SELECT * FROM items WHERE draft_id=%s AND better IS NOT NULL",
            (match.drid, )).fetchall()
        log.info("Applying %s items", len(items))

        # Blank out winnings
        c.execute("UPDATE bets SET winnings='{}' WHERE match=%s AND state>='CONFIRMED'",
            (match.mid, ))

        for idx, entry in enumerate(items):
            c.execute("""
                UPDATE bets SET winnings=array_append(winnings, %s::numeric), state='WON'
                WHERE match=%s AND state>='CONFIRMED' AND id=%s
            """, (entry.item_id, match.mid, entry.better))

