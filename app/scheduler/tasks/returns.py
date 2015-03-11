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
    with Cursor() as c:
        match = c.execute(FIND_MATCH_FOR_APPLY).fetchone()

        if not match:
            return

        # Take out our lock
        c.execute("UPDATE item_drafts SET state='USED' WHERE id=%s", (match.drid, ))

        # TODO: create checks to make sure its bueno

        with Cursor("fort_draft") as dc:
            items = dc.execute("SELECT * FROM items").fetchall()
            log.info("Applying %s items", len(items))

            for entry in dc.fetchall():
                c.execute("""
                    UPDATE bets SET winnings=array_append(winnings, %s::numeric), state='WON'
                    WHERE match=%s AND state='CONFIRMED'
                """, (entry.item_id, match.mid))

