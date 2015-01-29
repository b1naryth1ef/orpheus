from contextlib import contextmanager

import redis, psycopg2
from psycopg2.extras import NamedTupleCursor, Json

from emporium import app
from settings import CRYPT

class ValidationError(Exception):
    pass

def get_connection(database=None):
    return psycopg2.connect("host={host} port={port} dbname={dbname} user={user} password={pw}".format(
        host=app.config.get("PG_HOST"),
        port=app.config.get("PG_PORT"),
        dbname=database or app.config.get("PG_DATABASE"),
        user=app.config.get("PG_USERNAME"),
        pw=app.config.get("PG_PASSWORD")), cursor_factory=NamedTupleCursor)

def as_json(ctx):
    return Json(ctx)

@contextmanager
def transaction(database=None):
    conn = get_connection(database)
    cursor = conn.cursor()
    try:
        yield cursor
    except Exception as e:
        raise e
    else:
        conn.commit()
    finally:
        conn.close()

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

redis = redis.Redis(app.config.get("R_HOST"), port=app.config.get("R_PORT"), db=app.config.get("R_DB"))

