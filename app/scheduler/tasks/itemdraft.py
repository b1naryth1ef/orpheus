import logging, traceback

from datetime import datetime

from database import Cursor
from util.itemdraft import pre_draft, run_draft
from util.email import Email

log = logging.getLogger(__name__)

FIND_MATCH_DRAFT_QUERY = """
SELECT id, lock_date, match_date, teams FROM matches
WHERE lock_date < now() AND id NOT IN (
    SELECT match FROM item_drafts)
LIMIT 1;
"""

CREATE_ITEM_DRAFT = """
INSERT INTO item_drafts (match, team, state)
VALUES (%(match)s, %(team)s, %(state)s);
"""

def create_item_drafts():
    with Cursor() as c:
        match = c.execute(FIND_MATCH_DRAFT_QUERY).fetchone()

        if not match:
            return

        log.info("Creating new item drafts for match #%s", match.id)

        for team in match.teams:
            c.execute(CREATE_ITEM_DRAFT, {
                "match": match.id,
                "team": team,
                "state": "pending"
            })

FIND_ITEM_DRAFT_QUERY = """
SELECT id, match, team FROM item_drafts
WHERE state='pending'
"""

def run_item_drafts():
    with Cursor() as c:
        draft = c.execute(FIND_ITEM_DRAFT_QUERY).fetchone()

        if not draft:
            return

        # Let's make sure we don't get toe-stomped
        c.execute("UPDATE item_drafts SET state='started', started_at=now() WHERE id=%s", (draft.id, ))

        betters = c.execute(
            "SELECT id, better, value, items, team FROM bets WHERE match=%s", (draft.match, )).fetchall(as_list=True)

        # Calculate value so we can get return-value
        total_value = sum(map(lambda i: i.value, betters))
        winning_team_value = sum(map(lambda i: i.value if i.team == draft.team else 0, betters))

        draft_betters, draft_skins = [], []
        for better in betters:
            if better.team != draft.team:
                draft_skins += [(item.item_id, item.item_meta.get("price")) for item in better.items]
                continue

            draft_betters.append((better.id,
                ((total_value * 1.0) / winning_team_value) * better.value))


        log.info("[Draft #%s] starting pre-draft", draft.id)
        pre_draft(draft.id, draft_betters, draft_skins)

        log.info("[Draft #%s] running full draft", draft.id)
        run_draft(draft.id)

'''
def run_item_drafts():
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
'''
