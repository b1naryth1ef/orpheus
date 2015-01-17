from contextlib import contextmanager

from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import NamedTupleCursor, Json

from emporium import app
from settings import CRYPT

class PostgresDatabase(ThreadedConnectionPool):
    def __init__(self, conn, minc=1, maxc=12):
        ThreadedConnectionPool.__init__(self, minc, maxc, dsn=conn, cursor_factory=NamedTupleCursor)

def as_json(ctx):
    return Json(ctx)

@contextmanager
def transaction():
    conn = db.getconn()
    cursor = conn.cursor()
    try:
        yield cursor
    except Exception as e:
        raise e
    else:
        conn.commit()
    finally:
        db.putconn(conn)

db = PostgresDatabase("host={host} port={port} dbname=emporium user=emporium password={pw}".format(
    host=app.config.get("PG_HOST"),
    port=app.config.get("PG_PORT"),
    pw=CRYPT.get("postgres")))

