import logging
from datetime import datetime

from emporium import steam
from database import Cursor, redis

from util.steam import SteamAPIError

log = logging.getLogger(__name__)

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
    with Cursor() as c:
        now = datetime.utcnow()
        return c.execute(CREATE_USER_QUERY, (steamid, True, now, now, group, Cursor.json(DEFAULT_SETTINGS))).fetchone().id

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

def get_user_info(uid):
    if not uid:
        return {
            "authed": False
        }

    with Cursor() as c:
        resp = c.execute("SELECT steamid, settings, ugroup FROM users WHERE id=%s", (uid, )).fetchone()

    if not uid:
        return {
            "authed": False
        }

    try:
        nick = gache_nickname(resp.steamid)
    except SteamAPIError:
        log.exception("Failed to get and cache nickname (%s)" % resp.steamid)
        nick = ""

    return {
        "authed": True,
        "user": {
            "id": uid,
            "name": gache_nickname(resp.steamid),
            "steamid": str(resp.steamid),
            "settings": resp.settings,
            "group": resp.ugroup
        }
    }

