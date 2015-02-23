from datetime import datetime
from psycopg2.extras import Json

from database import Cursor
from util.errors import ValidationError
from helpers.user import UserGroup

def create_game(user, name, appid, meta=None, view_perm=UserGroup.NORMAL):
    if not isinstance(obj, dict):
        raise ValidationError("Game metadata must be dictionary")

    with Cursor() as c:
        return c.insert("games", {
            "name": name,
            "meta": as_json(meta or {}),
            "appid": appid,
            "view_perm": view_perm,
            "active": True,
            "created_by": user,
            "created_at": datetime.utcnow()
        }).fetchone().id

