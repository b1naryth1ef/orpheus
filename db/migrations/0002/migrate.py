"""
Migration #%(num)s
Added: %(date)s
"""

def before(db):
    pass

def during(db):
    c = db.cursor()
    c.execute("ALTER TYPE bot_status ADD VALUE 'NEEDGAME' BEFORE 'AVAIL'")
    db.commit()

def after(db):
    pass
