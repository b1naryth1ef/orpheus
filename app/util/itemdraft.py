"""
This is sort of not the best, but it works so #shipit
TODO:
    - create function to aggregate/load data from schema
"""

# TODO: fuck this
import os.path, sys, time
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from database import Cursor

def create_tables():
    with Cursor("emporium_draft") as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS betters (
            id SERIAL PRIMARY KEY,
            iid INTEGER,
            mid INTEGER,
            tid INTEGER,
            value REAL,
            needed REAL,
            current REAL
        );

        CREATE UNIQUE INDEX better_base ON betters (iid, mid, tid);
        CREATE INDEX better_needed ON betters (needed);
        CREATE INDEX better_team ON betters (tid);

        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            bid INTEGER,
            iid INTEGER,
            mid INTEGER,
            tid INTEGER,
            value REAL,
            better INTEGER REFERENCES betters
        );

        CREATE INDEX item_base ON items (bid, iid, mid, tid);
        CREATE INDEX item_value ON items (value);
        CREATE INDEX item_team ON items (tid);
        """)

CREATE_BETTER_SQL = """INSERT INTO betters
(iid, mid, tid, value, needed, current)
VALUES (%s, %s, %s, %s, %s, %s)"""
CREATE_ITEM_SQL = """INSERT INTO items
(bid, iid, mid, tid, value, better)
VALUES (%s, %s, %s, %s, %s, %s)"""

def pre_draft(match_id, team_id, betters, items):
    create_tables()

    with Cursor("emporium_draft") as c:
        c.execute("DELETE FROM items WHERE tid=%s", (team_id, ))
        c.execute("DELETE FROM betters WHERE tid=%s", (team_id, ))

        print "Inserting %s betters..." % len(betters)
        for (id, need) in betters:
            c.execute(CREATE_BETTER_SQL, (id, match_id, team_id, need, need, 0))

        print "Inserting %s items..." % len(items)
        for (betid, id, value) in items:
            c.execute(CREATE_ITEM_SQL, (betid, id, match_id, team_id, value, None))


ITEMS_FOR_DRAFT_QUERY = """
SELECT id, value FROM items WHERE mid=%s AND tid=%s AND better IS NULL ORDER BY value DESC
"""

def run_draft(match_id, team_id):
    c = Cursor("emporium_draft")
    items = c.execute(ITEMS_FOR_DRAFT_QUERY, (match_id, team_id)).fetchall(as_list=True)
    for i, item in enumerate(items):
        if not i % 100:
            print "  processing item #%s" % i
        draft_item(c, match_id, team_id, item)

GET_BETTER_FOR_ITEM = """
SELECT * FROM betters
WHERE needed >= %s
ORDER BY needed DESC LIMIT 1
"""

def draft_item(c, match_id, team_id, item):
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


if __name__ == "__main__":
    import random, time, sys

    create_tables()

    low_bins = map(lambda i: random.randint(50, 500) / 100.0, range(1, 10000))
    med_bins = map(lambda i: random.randint(5, 25), range(1, 45000))
    high_bins = map(lambda i: random.randint(25, 900), range(1, 5000))
    all_bins = map(lambda i: (i[0], i[1]), enumerate(low_bins + med_bins + high_bins))

    low_items = map(lambda i: random.randint(3, 500) / 100.0, range(1, 150000))
    med_items = map(lambda i: random.randint(5, 20), range(1, 90000))
    high_items = map(lambda i: random.randint(20, 300), range(1, 10000))
    all_items = map(lambda i: (i[0], i[1]), enumerate(low_items + med_items + high_items))

    if sum(map(lambda i: i[1], all_bins)) > sum(map(lambda i: i[1], all_items)):
        print "Won't work with random data..."
        sys.exit(1)

    with Cursor("emporium_draft") as c:
        base_id = c.execute("SELECT max(mid) as m FROM betters").fetchone().m or 0
        match_id = team_id = (base_id) + 1

    start = time.time()
    pre_draft(match_id, team_id, all_bins, all_items)
    print "Pre-draft took %ss" % (time.time() - start)

    start = time.time()
    run_draft(match_id, team_id)
    print "Draft Took %ss" % (time.time() - start)

