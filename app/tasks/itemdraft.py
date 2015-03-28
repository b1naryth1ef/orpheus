import logging, traceback

from datetime import datetime

from database import Cursor
from tasks import task

from util.itemdraft import pre_draft, run_draft
from util.email import Email

log = logging.getLogger(__name__)

# Grabs any locked matches where we haven't already created a draft
FIND_MATCH_DRAFT_QUERY = """
SELECT id, teams FROM matches
WHERE (state in ('LOCKED', 'WAITING', 'RESULT')) AND itemstate='LOCKED'
AND id NOT IN (SELECT match FROM item_drafts);
"""

@task()
def create_item_drafts():
    with Cursor() as c:
        for match in c.execute(FIND_MATCH_DRAFT_QUERY).fetchall():
            if not match:
                continue
            log.info("Creating new item drafts for match #%s", match.id)

            for team in match.teams:
                c.insert("item_drafts", {
                    "match": match.id,
                    "team": team,
                    "state": "PENDING"
                })

FIND_ITEM_DRAFT_QUERY = "SELECT id, match, team FROM item_drafts WHERE state='PENDING'"

FIND_AND_LOCK_ITEM_DRAFT = """
UPDATE item_drafts z
SET state='STARTED', started_at=now()
FROM (SELECT id FROM item_drafts WHERE state='PENDING' ORDER BY id LIMIT 1) AS draft
WHERE z.id=draft.id
RETURNING z.id, z.match, z.team
"""

@task()
def run_item_drafts():
    with Cursor() as c:
        draft = c.execute(FIND_AND_LOCK_ITEM_DRAFT).fetchone()

        # If we don't have any we're done
        if not draft:
            return

        # Grab all won bets
        won_bets = c.execute("""
            SELECT id, value FROM bets WHERE match=%s AND team=%s AND state='CONFIRMED'""",
            (draft.match, draft.team)).fetchall(as_list=True)

        # Grab all "lost" items
        lost_items = c.execute("""
            SELECT i.id, i.price FROM
                (SELECT unnest(b.items) AS item_id FROM bets b WHERE b.match=%s AND b.team!=%s AND state='CONFIRMED') b
                JOIN items i ON id=item_id""", (draft.match, draft.team)).fetchall(as_list=True)

        # Calculate the total value placed on the match
        total_value = c.execute(
            "SELECT sum(value) as v FROM bets WHERE match=%s", (draft.match, )).fetchone().v or 0

        # Calculate value of winning team
        winner_value = c.execute(
            "SELECT sum(value) as v FROM bets WHERE match=%s AND team=%s",
            (draft.match, draft.team)).fetchone().v or 0

        if not total_value or not winner_value:
            log.error("[Draft #%s] Cannot complete!", draft.id)
            c.execute("UPDATE item_drafts SET state='FAILED' WHERE id=%s", (draft.id, ))
            return

        value_mod = ((int(total_value) * 1.0) / int(winner_value))

        # Calculate return value for winners
        draft_bets = map(lambda i: (i.id, value_mod * int(i.value)), won_bets)

        try:
            log.info("[Draft #%s] starting pre-draft", draft.id)
            pre_draft(draft.id, draft_bets, lost_items)

            log.info("[Draft #%s] running full draft", draft.id)
            run_draft(draft.id)
            c.execute("UPDATE item_drafts SET state='COMPLETED' WHERE id=%s", (draft.id, ))
        except:
            log.exception("Item Draft %s Failed", draft.id)
            c.execute("UPDATE item_drafts SET state='FAILED' WHERE id=%s", (draft.id, ))

