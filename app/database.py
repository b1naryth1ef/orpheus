from contextlib import contextmanager

import redis
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import NamedTupleCursor, Json

from emporium import app
from settings import CRYPT

class ValidationError(Exception):
    pass

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

def select(obj, *fields, **params):
    query = "SELECT %s FROM %s" % (', '.join(fields), obj)

    if len(params):
        etc = ' AND '.join(map(lambda k: "{}=%({})s".format(k, k), params.keys()))
        query += " WHERE %s" % etc

    return query, params

def map_db_values(obj):
    return ', '.join(map(lambda i: i+"=%("+i+")s", obj.keys()))

def tranf(f):
    def deco(*args, **kwargs):
        with transaction() as t:
            return f(t, *args, **kwargs)
    return deco

db = PostgresDatabase("host={host} port={port} dbname={dbname} user={user} password={pw}".format(
    host=app.config.get("PG_HOST"),
    port=app.config.get("PG_PORT"),
    dbname=app.config.get("PG_DATABASE"),
    user=app.config.get("PG_USERNAME"),
    pw=app.config.get("PG_PASSWORD")))

redis = redis.Redis(app.config.get("R_HOST"), port=app.config.get("R_PORT"), db=app.config.get("R_DB"))

