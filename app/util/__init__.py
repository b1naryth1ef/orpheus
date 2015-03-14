import decimal, random
from flask import flash, redirect
from psycopg2.extensions import adapt, register_adapter, AsIs

class BaseEnum(object):
    pass

class EnumAttr(object):
    def __init__(self, parent, content, index):
        self.parent = parent
        self.content = content
        self.index = index

    def __eq__(self, other):
        if isinstance(other, EnumAttr):
            (self.index == other.index) or (self.content == other.content)

        if isinstance(other, int):
            if self.index == other:
                return True

        return self.content == other

    def __cmp__(self, other):
        if isinstance(other, EnumAttr):
            return self.index - other.index

        if isinstance(other, int):
            return self.index - other

        return self.index - self.parent.ORDER.index(other)

    def __repr__(self):
        return self.content

    def __str__(self):
        return self.content

    @staticmethod
    def psycopg2_adapt(obj):
        return AsIs("'" + str(obj) + "'")

def create_enum(*args):
    class _T(BaseEnum):
        ORDER = args

    for index, entry in enumerate(args):
        setattr(_T, entry, EnumAttr(_T, entry, index))

    return _T

register_adapter(EnumAttr, EnumAttr.psycopg2_adapt)


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

def convert_steamid(id):
    if len(id) == 17:
        return int(id[3:]) - 61197960265728
    else:
        return '765' + str(int(id) + 61197960265728)

