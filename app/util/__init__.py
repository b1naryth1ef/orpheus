import decimal
from flask import flash, redirect

class BaseEnum(object):
    pass

def create_enum(*args):
    class _T(BaseEnum):
        ORDER = args

    for entry in args:
        setattr(_T, entry, entry)

    return _T

def flashy(m, f="danger", u="/"):
    flash(m, f)
    return redirect(u)

class SimpleObject(object):
    def __init__(self, data):
        self.__dict__.update(data)

def paginate(page, per_page=25):
    """
    Returns a (limit, offset) combo for pagination
    """
    if page > 0:
        page -= 1

    return per_page, page * per_page

def json_encoder(obj):
    if isinstance(obj, decimal.Decimal):
        return str(float(obj))
    raise Exception("Unsupported type: %s" % obj.__class__.__name__)
