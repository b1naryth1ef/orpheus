from database import redis
from emporium import steam

class SimpleObject(object):
    def __init__(self, data):
        self.__dict__.update(data)

def paginate(page, per_page=25):
    """
    Returns a (limit, offset) combo for pagination
    """
    if page > 0:
        page -= 1

    return per_page, page * per_page

def get_or_cache_nickname(steamid):
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
