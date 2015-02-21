import logging, re
from datetime import datetime

from emporium import steam
from database import Cursor, redis

from util import create_enum
from util.steam import SteamAPIError

log = logging.getLogger(__name__)

class InvalidTradeUrl(Exception): pass

UserGroup = create_enum('NORMAL', 'MODERATOR', 'ADMIN', 'SUPER')

DEFAULT_SETTINGS = {
    "ui": {
        "disable_streams": False,
        "disable_push": False
    }
}

USER_SETTING_SAVE_PARAMS = [
    "trade_url", "ui.disable_streams", "ui.disable_push"
]


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
        resp = c.execute("SELECT steamid, settings, ugroup, trade_token FROM users WHERE id=%s", (uid, )).fetchone()

    if not uid:
        return {
            "authed": False
        }

    try:
        nick = gache_nickname(resp.steamid)
    except SteamAPIError:
        log.exception("Failed to get and cache nickname (%s)" % resp.steamid)
        nick = ""

    # Rebuild the trade url because UX
    resp.settings['trade_url'] = 'https://steamcommunity.com/tradeoffer/new/?partner=%s&token=%s' % (
        resp.steamid, resp.trade_token)

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

INSERT_BOTH_SETTINGS = """
UPDATE users SET settings=%s, trade_token=%s WHERE id=%s
"""

INSERT_ONLY_SETTINGS = """
UPDATE users SET settings=%s WHERE id=%s
"""

def user_save_settings(uid, obj):
    assert(isinstance(obj["ui.disable_streams"], bool))
    assert(isinstance(obj["ui.disable_push"], bool))

    trade_url = obj.get('trade_url')
    obj = {
        "ui": {
            "disable_streams": obj["ui.disable_streams"],
            "disable_push": obj["ui.disable_push"],
       }
    }

    with Cursor() as c:
        if trade_url:
            token = re.findall("token=([a-zA-Z0-9\-]+)", trade_url)
            if len(token) != 1:
                raise InvalidTradeUrl("Invalid trade_url")
            c.execute(INSERT_BOTH_SETTINGS, (Cursor.json(obj), token[0], uid))
        else:
            c.execute(INSERT_ONLY_SETTINGS, (Cursor.json(obj), uid))

