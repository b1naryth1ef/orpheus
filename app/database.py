import logging, redis, psycopg2, random, string
from contextlib import contextmanager

from flask import g
from psycopg2.extras import NamedTupleCursor, Json

from fort import app

log = logging.getLogger(__name__)

redis = redis.Redis(
    app.config.get("R_HOST"),
    port=app.config.get("R_PORT"),
    db=app.config.get("R_DB"))

psycopg2.extras.register_uuid()

DATABASES = {}

# The base connection string
PG_CONN_STRING = "host={host} port={port} user={user} password={pw} connect_timeout=5".format(
    host=app.config.get("PG_HOST"),
    port=app.config.get("PG_PORT"),
    user=app.config.get("PG_USERNAME"),
    pw=app.config.get("PG_PASSWORD"))


def get_connection(database='fort'):
    """
    Returns a psycopg2 postgres connection. In production this will
    hit PGBouncer, and be pooled. `database` can be a valid database name.
    """
    if database not in DATABASES or DATABASES[database].closed:
        dbc = psycopg2.connect(PG_CONN_STRING + " dbname={}".format(database),
            cursor_factory=NamedTupleCursor)

        dbc.autocommit = True
        DATABASES[database] = dbc
    return DATABASES[database]

def random_savepoint_id():
    return ''.join([random.choice(string.letters) for _ in range(32)])

class ResultSetIterable(object):
    """
    Represents a set of results from a postgres query. Generator
    that is used to cache the result set in memory for multiple
    iterations.
    """
    def __init__(self, cursor):
        self.cursor = cursor
        self.size = self.cursor.rowcount
        self.index = 0

    def __len__(self):
        return self.size

    def __iter__(self):
        return self

    def next(self):
        if self.index >= self.size:
            raise StopIteration()

        self.index += 1
        return self.cursor.fetchone()

class Cursor(object):
    """
    A base class that can be used to query the PG database. Generally
    all database actions should be take through this. A single cursor
    should be used for the duration of a request, errors and exceptions
    are scoped within the context of the cursor, allow rollback semantics.
    """
    def __init__(self, database='fort'):
        self.db = get_connection(database)
        self.cursor = self.db.cursor()
        self.savepoint = None

    @staticmethod
    def json(obj):
        return Json(obj)

    @staticmethod
    def map_values(obj):
        return ', '.join(map(lambda i: i+"=%("+i+")s", obj.keys()))

    def close(self):
        self.cursor.close()

    def execute(self, *args, **kwargs):
        self.cursor.execute(*args, **kwargs)
        return self

    def fetchone(self, *args, **kwargs):
        return self.cursor.fetchone()

    def mogrify(self, *args, **kwargs):
        return self.cursor.mogrify(*args, **kwargs)

    def fetchall(self, as_list=False):
        if as_list:
            return self.cursor.fetchall()

        return ResultSetIterable(self.cursor)

    def commit(self):
        self.db.commit()

    def __enter__(self):
        if self.db.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
            self.savepoint = random_savepoint_id()
            self.cursor.execute("SAVEPOINT %s" % self.savepoint)
        else:
            self.db.set_session(autocommit=False)
        return self

    def __exit__(self, typ, value, tb):
        if value != None:
            if self.savepoint:
                self.cursor.execute("ROLLBACK TO SAVEPOINT %s" % self.savepoint)
            else:
                self.db.rollback()
                self.db.set_session(autocommit=True)
            return False

        if not self.savepoint:
            self.db.commit()
            self.db.set_session(autocommit=True)

        self.cursor.close()

    def count(self, obj, where=None, *args):
        Q = "SELECT count(*) as c FROM %s" % obj

        if where:
            Q = Q + " WHERE %s" % where
        return self.execute(Q, *args).fetchone().c

    def select(self, obj, *fields, **params):
        query = "SELECT %s FROM %s" % (', '.join(fields), obj)

        if len(params):
            etc = ' AND '.join(map(lambda k: "{}=%({})s".format(k, k), params.keys()))
            query += " WHERE %s" % etc

        return self.execute(self.cursor.mogrify(query, params))

    def update(self, table, id, obj=None, **kwargs):
        obj = obj or kwargs

        query_string = "UPDATE {table} SET {sets} WHERE id=%s;".format(
            table=table,
            sets=', '.join(map(lambda i: "{}=%s".format(i[0]), obj.items()))
        )

        obj = obj.values() + [id]
        return self.execute(query_string, tuple(obj)).cursor.rowcount

    def insert(self, table, obj=None, **kwargs):
        obj = obj or kwargs

        query_string = "INSERT INTO {table} ({keys}) VALUES ({values}) RETURNING id;".format(
            table=table,
            keys=', '.join(obj.keys()),
            values=', '.join(map(lambda i: "%({})s".format(i), obj.keys()))
        )

        return self.execute(query_string, obj).fetchone().id

    def paramify(self, obj):
        return ', '.join(obj.keys()), ', '.join(map(lambda i: "%({})s".format(i), obj.keys()))

