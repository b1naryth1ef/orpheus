from contextlib import contextmanager

import logging, redis, psycopg2
from flask import g
from psycopg2.extras import NamedTupleCursor, Json

from emporium import app
from settings import CRYPT

from util.custom import bind_custom_types

CONNECTIONS = {}

log = logging.getLogger(__name__)
redis = redis.Redis(app.config.get("R_HOST"), port=app.config.get("R_PORT"), db=app.config.get("R_DB"))

def get_connection(database=None):
    """
    Attempts to get a cached connection, or create a brand new connection to the database `database`
    """
    if database not in CONNECTIONS or CONNECTIONS[database].closed:
        log.info("Connecting to database %s" % database)
        dbc = psycopg2.connect("host={host} port={port} dbname={dbname} user={user} password={pw}".format(
            host=app.config.get("PG_HOST"),
            port=app.config.get("PG_PORT"),
            dbname=database or app.config.get("PG_DATABASE"),
            user=app.config.get("PG_USERNAME"),
            pw=app.config.get("PG_PASSWORD")), cursor_factory=NamedTupleCursor)
        bind_custom_types(dbc)
        dbc.autocommit = True
        CONNECTIONS[database] = dbc

    return CONNECTIONS[database]

class ResultSetIterable(object):
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
    def __init__(self, database=None, commit=False):
        self.db = get_connection(database)
        self.commit = commit
        self.cursor = self.db.cursor()

    @staticmethod
    def json(obj):
        return Json(obj)

    @staticmethod
    def map_values(self, obj):
        return ', '.join(map(lambda i: i+"=%("+i+")s", obj.keys()))

    def close(self):
        self.cursor.close()

    def execute(self, *args, **kwargs):
        self.cursor.execute(*args, **kwargs)
        return self

    def fetchone(self, *args, **kwargs):
        return self.cursor.fetchone()

    def fetchall(self, as_list=False):
        if as_list:
            return self.cursor.fetchall()

        return ResultSetIterable(self.cursor)

    def __enter__(self):
        return self

    def __exit__(self, typ, value, tb):
        if value != None:
            raise value

        if self.commit:
            self.db.commit()

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

