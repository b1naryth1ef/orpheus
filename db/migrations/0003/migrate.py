
def before(db):
    pass

def during(db):
    c = db.cursor()
    c.execute("ALTER TABLE items ALTER COLUMN owner TYPE varchar(255) USING owner::varchar;") 

def after(db):
    pass
