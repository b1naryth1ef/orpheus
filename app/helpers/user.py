from datetime import datetime

from database import transaction, as_json

class UserGroup(object):
    NORMAL = 'normal'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    SUPER = 'super'

DEFAULT_SETTINGS = {

}

def create_user(steamid, group=UserGroup.NORMAL):
    """
    Attempts to create a user based on their steamid, and optionally a group.
    This expectes to fail if the steamid already exists, and will raise `psycopg2.IntegrityError`
    when it does.
    """
    with transaction() as t:
        t.execute("INSERT INTO users (steamid, active, join_date, ugroup, settings) VALUES (%s, %s, %s, %s, %s) RETURNING id", (
            steamid, True, datetime.utcnow(), group, as_json(DEFAULT_SETTINGS) 
        ))

        return t.fetchone().id
