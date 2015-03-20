import uuid, traceback, sys
from datetime import datetime
from database import Cursor

CREATE_EXCEPTION_SQL = """
INSERT INTO exceptions (id, etype, content, meta, created_at)
VALUES (%s, %s, %s, %s, %s)
"""

def create_exception(exception, meta):
    """
    Attempts to insert an exception into the database. Does not fail gracefully,
    and will bubble exceptions to the caller.
    """
    id = uuid.uuid4()
    exc_type, exc_obj, exc_tb = sys.exc_info()

    content = ''.join(traceback.format_exception(exc_type, exc_obj, exc_tb))

    with Cursor() as c:
        c.execute(CREATE_EXCEPTION_SQL, (
            id, str(exc_type), content, Cursor.json(meta),
            datetime.utcnow()))

    return id

def get_enum_array(enum_type):
    with Cursor() as c:
        return c.execute(
            "SELECT unnest(enum_range(NULL::{}))".format(enum_type)
        ).fetchall(as_list=True)

