import logging

from database import Cursor

log = logging.getLogger(__name__)

CREATE_BETTER_SQL = """INSERT INTO betters
(id, draft_id, value, needed, current)
VALUES (%(id)s, %(draft_id)s, %(value)s, %(needed)s, %(current)s)"""

CREATE_ITEM_SQL = """INSERT INTO items
(draft_id, item_id, value, better)
VALUES (%(draft_id)s, %(item_id)s, %(value)s, %(better)s)"""

def pre_draft(draft, betters, items):
    with Cursor("fort_draft") as c:
        log.info("Deleting old draft data...")

        # This is in theory dangerous, might wanna change it at some point
        c.execute("DELETE FROM items WHERE draft_id=%s", (draft, ))
        c.execute("DELETE FROM betters WHERE draft_id=%s", (draft, ))

        log.info("Inserting %s betters..." % len(betters))
        for (id, need) in betters:
            c.execute(CREATE_BETTER_SQL, {
                "id": id,
                "draft_id": draft,
                "value": need,
                "needed": need,
                "current": 0
            })

        log.info("Inserting %s items..." % len(items))
        for (id, value) in items:
            c.execute(CREATE_ITEM_SQL, {
                "draft_id": draft,
                "item_id": id,
                "value": value,
                "better": None
            })

ITEMS_FOR_DRAFT_QUERY = """
SELECT id, value FROM items WHERE draft_id=%s AND better IS NULL ORDER BY value DESC
"""
def run_draft(draft):
    c = Cursor("fort_draft")
    items = c.execute(ITEMS_FOR_DRAFT_QUERY, (draft, )).fetchall(as_list=True)
    for i, item in enumerate(items):
        if not i % 100:
            log.info("  processing item #%s" % i)
        draft_item(c, draft, item)

GET_BETTER_FOR_ITEM = """
SELECT * FROM betters
WHERE needed >= %s AND draft_id=%s
ORDER BY needed DESC LIMIT 1
"""

def draft_item(c, id, item):
    entry = c.execute(GET_BETTER_FOR_ITEM, (item.value, id)).fetchone()

    if not entry:
        return

    current = entry.current + item.value
    needed = entry.value - current

    # Update item, we've now allocated it
    c.execute("UPDATE items SET better=%s WHERE id=%s AND draft_id=%s", (entry.id, item.id, id))

    # Update better
    c.execute("UPDATE betters SET current=%s, needed=%s WHERE id=%s AND draft_id=%s", (
        current, needed, entry.id, id
    ))

