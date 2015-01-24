import functools

from flask import g

from helpers.user import UserGroup
from util.errors import UserError, APIError

def authed(group=UserGroup.NORMAL):
    def deco(f):
        base_group_index = UserGroup.ORDER.index(group)

        @functools.wraps(f)
        def _f(*args, **kwargs):
            if not g.user or not g.group:
                raise UserError("You must be logged in for that!", "error")

            group_index = UserGroup.ORDER.index(g.group)

            if group_index < base_group_index:
                raise UserError("You don't have permission to see that!", "error")
            return f(*args, **kwargs)
        return _f
    return deco

