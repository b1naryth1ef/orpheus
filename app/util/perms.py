import functools

from flask import g

from util.errors import UserError, APIError

def authed(group):
    def deco(f):
        @functools.wraps(f)
        def _f(*args, **kwargs):
            if not g.user or not g.group:
                return UserError("You must be logged in for that!", "error")
            
            if g.group not in group:
                return UserError("You don't have permission to see that!", "error")
            return f(*args, **kwargs)
        return _f
    return deco

