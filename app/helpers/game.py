from datetime import datetime

from database import transaction, as_json, ValidationError
from helpers.user import UserGroup

CREATE_GAME_SQL = """
INSERT INTO games (name, meta, appid, view_perm, active, created_by, created_at)
VALUES (%(name)s, %(meta)s, %(appid)s, %(view_perm)s, %(active)s, %(created_by)s, %(created_at)s)
RETURNING id
"""

def validate_game_metadata(obj):
    if not isinstance(obj, dict):
        raise ValidationError("Game metadata must be dictionary")

    return True

def create_game(user, name, appid, meta=None, view_perm=UserGroup.NORMAL):
    validate_game_metadata(meta)

    with transaction() as t:
        t.execute(CREATE_GAME_SQL, {
            "name": name,
            "meta": as_json(meta or {}),
            "appid": appid,
            "view_perm": view_perm,
            "active": True,
            "created_by": user,
            "created_at": datetime.utcnow()
        })

        return t.fetchone().id

