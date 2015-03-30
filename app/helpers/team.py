from database import Cursor
from datetime import datetime
from util.errors import APIError

from helpers.user import gache_user_info

def team_to_json(entry):
    return {
            "id":entry.id,
            "tag":entry.tag,
            "name":entry.name,
            "logo": entry.logo
    }
