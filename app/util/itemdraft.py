import logging

from database import Cursor

log = logging.getLogger(__name__)

def create_tables():
    with Cursor("draft") as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS betters (
            id INTEGER PRIMARY KEY,
            draft_id INTEGER,
            value REAL,
            needed REAL,
            current REAL
        );

        CREATE UNIQUE INDEX better_base ON betters (id, draft_id);
        CREATE INDEX better_needed ON betters (needed);

        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            draft_id INTEGER,
            item_id INTEGER,
            value REAL,
            better INTEGER REFERENCES betters
        );

        CREATE INDEX item_base ON items (id, draft_id, item_id);
        CREATE INDEX item_value ON items (value);
        """)

CREATE_BETTER_SQL = """INSERT INTO betters
(id, draft_id, value, needed, current)
VALUES (%(id)s, %(draft_id)s, %(value)s, %(needed)s, %(current)s)"""

CREATE_ITEM_SQL = """INSERT INTO items
(draft_id, item_id, value, better)
VALUES (%(draft_id)s, %(item_id)s, %(value)s, %(better)s)"""

def pre_draft(draft, betters, items):
    create_tables()

    with Cursor("draft") as c:
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
    c = Cursor("draft")
    items = c.execute(ITEMS_FOR_DRAFT_QUERY, (draft, )).fetchall(as_list=True)
    for i, item in enumerate(items):
        if not i % 100:
            log.info("  processing item #%s" % i)
        draft_item(c, item)

GET_BETTER_FOR_ITEM = """
SELECT * FROM betters
WHERE needed >= %s
ORDER BY needed DESC LIMIT 1
"""

def draft_item(c, item):
    entry = c.execute(GET_BETTER_FOR_ITEM, (item.value, )).fetchone()

    if not entry:
        return

    current = entry.current + item.value
    needed = entry.value - current

    # Update item, we've now allocated it
    c.execute("UPDATE items SET better=%s WHERE id=%s", (entry.id, item.id, ))

    # Update better
    c.execute("UPDATE betters SET current=%s, needed=%s WHERE id=%s", (
        current, needed, entry.id,
    ))

