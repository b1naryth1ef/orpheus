"""
Migration #0003
Added: 1427738291.28
"""

def before(db):
    c = db.cursor()
    c.execute("ALTER TABLE trades ADD COLUMN expires_at  timestamp;")

def during(db):
    c = db.cursor()
    c.execute("UPDATE trades SET expires_at=created_at + interval '15 minutes' WHERE expires_at IS NULL")

def after(db):
    pass
