from flask import flash, redirect

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

