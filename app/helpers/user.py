import functools, logging, re, json
from datetime import datetime

from flask import g

from fort import steam
from database import Cursor, redis

from util import create_enum, convert_steamid
from util.steam import SteamAPIError
from util.errors import UserError, APIError, InvalidTradeUrl

log = logging.getLogger(__name__)

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

def create_user(steamid, group=UserGroup.NORMAL):
    """
    Attempts to create a user based on their steamid, and optionally a group.
    This expectes to fail if the steamid already exists, and will raise `psycopg2.IntegrityError`
    when it does.
    """
    with Cursor() as c:
        now = datetime.utcnow()
        return c.insert("users", {
            "steamid": steamid,
            "active": True,
            "join_date": now,
            "last_login": now,
            "ugroup": group,
            "settings": Cursor.json(DEFAULT_SETTINGS)
        }).fetchone().id

def build_error(msg, typ, api=False):
    if api:
        return APIError(msg)
    else:
        return UserError(msg, typ)

def authed(group=UserGroup.NORMAL, api=False):
    def deco(f):
        base_group_index = UserGroup.ORDER.index(group)

        @functools.wraps(f)
        def _f(*args, **kwargs):
            if not g.user or not g.group:
                raise build_error("You must be logged in for that!", "error", api)

            group_index = UserGroup.ORDER.index(g.group)

            if group_index < base_group_index:
                raise build_error("You don't have permission to see that!", "error", api)
            return f(*args, **kwargs)
        return _f
    return deco

def gache_user_info(steamid):
    """
    Gets the steam users info, or retreives a cached version of it.
    Cache time: 30 minutes
    """
    info = redis.get("u:%s:info" % steamid)

    if info:
        info = json.loads(info)
    else:
        info = steam.getUserInfo(steamid)

        # Turn a profileurl into just the vanity name
        if 'profileurl' in info:
            info['vanityname'] = info['profileurl'].rsplit("/", 2)[1]

        redis.setex("u:%s:info" % steamid, json.dumps(info), 60 * 30)
    return info

def get_user_info(uid):
    if not uid:
        return {
            "authed": False
        }

    with Cursor() as c:
        resp = c.execute("SELECT steamid, settings, ugroup, trade_token FROM users WHERE id=%s",
            (uid, )).fetchone()

    if not uid:
        return {
            "authed": False
        }

    try:
        steam_info = gache_user_info(resp.steamid)
    except SteamAPIError:
        log.exception("Failed to get and cache nickname (%s)" % resp.steamid)
        info = {}


    # Rebuild the trade url because UX
    resp.settings['trade_url'] = 'https://steamcommunity.com/tradeoffer/new/?partner=%s&token=%s' % (
        convert_steamid(resp.steamid), resp.trade_token) if resp.trade_token else ""

    return {
        "authed": True,
        "user": {
            "id": uid,
            "name": steam_info.get("personaname"),
            "vanity": steam_info.get("vanityname"),
            "steamid": str(resp.steamid),
            "settings": resp.settings,
            "group": resp.ugroup,
            "token": resp.trade_token
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
            comps = dict(re.findall("([a-zA-Z0-9\-]+)=([a-zA-Z0-9\-]+)", trade_url))

            if u'token' not in comps or u'partner' not in comps:
                raise InvalidTradeUrl("maliformed URL")

            # Grab the users steamid
            user = c.execute("SELECT steamid FROM users WHERE id=%s", (uid, )).fetchone()

            if convert_steamid(comps['partner']) != user.steamid:
                raise InvalidTradeUrl("trade url is for the wrong account")
            c.execute(INSERT_BOTH_SETTINGS, (Cursor.json(obj), comps['token'], uid))
        else:
            c.execute(INSERT_ONLY_SETTINGS, (Cursor.json(obj), uid))

