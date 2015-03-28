from database import Cursor
from datetime import datetime
from util.errors import APIError

from helpers.user import gache_user_info

def value_history_to_json(entry):
    return {
            "value":entry.value,
            "match_date":entry.match_date.isoformat(),
            "team":entry.team,
            "won": entry.won
    }
