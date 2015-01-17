from datetime import datetime

from database import transaction, as_json

class UserGroup(object):
    NORMAL = 'normal'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    SUPER = 'super'

DEFAULT_SETTINGS = {

}

CREATE_USER_QUERY = """
    INSERT INTO users (steamid, active, join_date, last_login, ugroup, settings) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
"""

class UserHelper(object):
    @classmethod
    def cache_nickname(cls, steamid):
        """
        Caches a users steam nickname in redis. Nicknames are kept for 2
        hours (120 minutes), and then expired. This function will also
        return the latest steamid after caching, to allow for getandset
        functionality
        """
        data = steam.getUserInfo(steamid)
        red.setex("nick:%s" % steamid, data["personaname"], 60 * 120)
        return data['personaname']
    
    @classmethod
    def get_nickname(cls, steamid):
        """
        Returns the nickname. This will read from the cache if it exists,
        or will set the cache if it does not.
        NB: might be worth asyncing this out to a job if the steamapi is
        down or slow!
        """
        if not hasattr(self, "nickname"):
            self.nickname = red.get("nick:%s" % self.steamid) or self.cache_nickname(self.steamid)
            if not isinstance(self.nickname, unicode):
                self.nickname = self.nickname.decode('utf-8')
        return self.nickname

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
