import functools

from flask import g

from helpers.user import UserGroup
from util.errors import UserError, APIError

def build_error(msg, typ, api=False):
    if api:
        return APIError(msg)
    else:
        return UserError(msg, typ)

def authed(group=UserGroup.NORMAL, api=False):
    def deco(f):
        base_group_index = UserGroup.ORDER.index(group)

        @functools.wraps(f)
        def _f(*args, **kwargs):
            if not g.user or not g.group:
                raise build_error("You must be logged in for that!", "error", api)

            group_index = UserGroup.ORDER.index(g.group)

            if group_index < base_group_index:
                raise build_error("You don't have permission to see that!", "error", api)
            return f(*args, **kwargs)
        return _f
    return deco

