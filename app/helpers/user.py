from datetime import datetime

from database import transaction, as_json

class UserGroup(object):
    NORMAL = 'normal'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    SUPER = 'super'

DEFAULT_SETTINGS = {}

CREATE_USER_QUERY = """
    INSERT INTO users (steamid, active, join_date, last_login, ugroup, settings) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
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

