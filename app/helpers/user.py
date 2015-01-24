from datetime import datetime

from emporium import steam
from database import transaction, as_json, redis

class UserGroup(object):
    NORMAL = 'normal'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    SUPER = 'super'

    ORDER = [NORMAL, MODERATOR, ADMIN, SUPER]

DEFAULT_SETTINGS = {}

CREATE_USER_QUERY = """
INSERT INTO users (steamid, active, join_date, last_login, ugroup, settings)
VALUES (%s, %s, %s, %s, %s, %s)
RETURNING id
"""

def create_user(steamid, group=UserGroup.NORMAL):
    """
    Attempts to create a user based on their steamid, and optionally a group.
    This expectes to fail if the steamid already exists, and will raise `psycopg2.IntegrityError`
    when it does.
    """
    with transaction() as t:
        now = datetime.utcnow()
        t.execute(CREATE_USER_QUERY, (steamid, True, now, now, group, as_json(DEFAULT_SETTINGS)))
        return t.fetchone().id

def gache_nickname(steamid):
    """
    Gets a steam nickname either from the cache, or the steam API. It
    then ensures it's cached for 2 hours.
    """
    nick = redis.get("nick:%s" % steamid)
    if not nick:
        nick = steam.getUserInfo(steamid)['personaname']
        redis.setex("nick:%s" % steamid, nick, 60 * 120)

    if not isinstance(nick, unicode):
        nick = nick.decode("utf-8")

    return nick

