"""
Migration #0002
Added: 1427611902.69
"""

CREATE_TABLES = """
CREATE TYPE return_state AS ENUM ('PENDING', 'RETURNED', 'LOCKED');

CREATE TABLE returns (
  id         SERIAL PRIMARY KEY,
  state      return_state NOT NULL,
  match      integer references matches(id),
  owner      integer references users(id),
  trade      integer references trades(id),
  item_type  integer references itemprices(id),
  item_id    numeric
);
"""

def before(db):
    c = db.cursor()
    c.execute(CREATE_TABLES)

NEED_RETURN = """
SELECT items, winnings, match, better FROM bets WHERE state='WON'
"""

def add_return(c, obj):
    c.execute("""
        INSERT INTO returns (state, match, owner, item_type)
        VALUES (%(state)s, %(match)s, %(owner)s, %(item_type)s)
    """, obj)

def get_item_type(c, id):
    c.execute("""
        SELECT ip.id FROM items i
        JOIN itemprices ip ON ip.name=i.name
        WHERE i.id=%s
    """, (id, ))
    t = c.fetchone()

    if not t:
        return -1

    return t

def during(db):
    c = db.cursor()
    c.execute(NEED_RETURN)

    for entry in c.fetchall():
        items = (entry[0] or []) + (entry[1] or [])
        for item in items:
            add_return(c, {
                "state": "PENDING",
                "match": entry[2],
                "owner": entry[3],
                "item_type": get_item_type(c, item),
            })

def after(db):
    pass
