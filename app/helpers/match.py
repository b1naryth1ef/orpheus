from datetime import datetime

from database import transaction, as_json, ValidationError
from helpers.user import UserGroup

CREATE_MATCH_SQL = """
INSERT INTO matches (game, teams, meta, results, lock_date, match_date, public_date, view_perm, active, created_at, created_by)
VALUES (%(game)s, %(teams)s, %(meta)s, %(results)s, %(lock_date)s, %(match_date)s, %(public_date)s,
%(view_perm)s, %(active)s, %(created_at)s, %(created_by)s)
RETURNING id;
"""

def validate_match_team_data(obj):
    if not isinstance(obj, list):
        raise ValidationError("Team data must be a list")

    if not len(obj) > 2:
        raise ValidationError("Team data must containt at least two teams")

    if not all(map(lambda i: i.get("name"), obj)):
        raise ValidationError("Teams in team data must contain at least a name")

    if not all(map(lambda i: isinstance(i.get("players"), list), obj)):
        raise ValidationError("Teams must have a list of players (can be empty")

    return True

def validate_match_meta_data(obj):
    if not isinstance(obj, dict):
        raise ValidationError("Match meta data must be a dictionary")

    return True

def create_match(user, game, teams, meta, lock_date, match_date, public_date, view_perm=UserGroup.NORMAL):
    validate_match_team_data(teams)

    with transaction() as t:
        t.execute(CREATE_MATCH_SQL, {
            "game": game,
            "teams": teams,
            "meta": meta,
            "results": as_json({}),
            "lock_date": lock_date,
            "match_date": match_date,
            "public_date": public_date,
            "view_perm": view_perm,
            "active": False,
            "created_at": datetime.utcnow(),
            "created_by": user
        })

        return t.fetchone().id


