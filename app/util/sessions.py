import json, time, logging

from uuid import uuid4
from flask import request

from database import redis

log = logging.getLogger(__name__)

# 5 days
SESSION_TTL = 60 * 60 * 24 * 5

class Session(object):
    def __init__(self, id=None):
        self._id = id or request.cookies.get("s")
        if self._id and redis.exists("session:%s" % self._id):
            log.debug('loading session %s', self._id)
            self._data = json.loads(redis.get("session:%s" % self._id))
        else:
            self._id = None
            self._data = {}
        self._changed = False

    def delete(self, item):
        self._changed = True
        if item in self._data:
            del self._data[item]

    def get(self, item, default=None):
        return self._data.get(item, default)

    def __delitem__(self, item):
        self._changed = True
        del self._data[item]

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, item, value):
        self._changed = True
        self._data[item] = value

    def save(self, response):
        if not self._changed:
            log.debug('not saving session; it remains unchanged')
            return

        # TODO: pipeline/setex
        self._id = self._id or str(uuid4())
        ttl = int(redis.ttl("session:%s" % self._id) or SESSION_TTL)

        # TODO: domain?
        response.set_cookie("s", self._id, expires=(time.time() + ttl))

        log.debug('saving session %s', self._id)
        redis.set("session:%s" % self._id, json.dumps(self._data))
        redis.expire("session:%s" % self._id, ttl if ttl != -1 else SESSION_TTL)
        return True

