from database import transaction, as_json

def get_count(table):
    with transaction() as t:
        t.execute("SELECT count(*) as c FROM %s" % table)
        return t.fetchone().c


