
def before(db):
    pass

def during(db):
    cursor = db.cursor()
    cursor.execute("ALTER TABLE bots ADD COLUMN token varchar(32)")
    db.commit()

def after(db):
    pass
