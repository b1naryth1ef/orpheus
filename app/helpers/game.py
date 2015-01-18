from datetime import datetime

from database import transaction, as_json
from helpers.user import UserGroup 

CREATE_GAME_SQL = """
INSERT INTO games (name, appid, view_perm, active, created_by, created_at)
VALUES %(name)s, %(appid)s, %(view_perm)s, %(active)s, %(created_by)s, %(created_at)s
RETURNING id;
"""

def create_game(user, name, appid, view_perm=UserGroup.NORMAL):
    with transaction() as t:
        t.execute(CREATE_GAME_SQL, {
            "name": name,
            "appid": appid,
            "view_perm": view_perm,
            "created_by": user,
            "created_at": datetime.utcnow()
        })

        return t.fetchone().id

