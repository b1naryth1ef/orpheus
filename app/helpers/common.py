import uuid, traceback, sys
from datetime import datetime
from database import Cursor

CREATE_EXCEPTION_SQL = """
INSERT INTO exceptions (id, etype, content, meta, created_at)
VALUES (%s, %s, %s, %s, %s)
"""

def create_exception(exception, meta):
    id = uuid.uuid4()
    exc_type, exc_obj, exc_tb = sys.exc_info()

    with Cursor() as c:
        c.execute(CREATE_EXCEPTION_SQL, (
            id, str(exc_type),
            ' '.join(traceback.format_exception(exc_tb)), Cursor.json(meta),
            datetime.utcnow()))

    return id, traceback.format_exception(exc_type, exc_obj, exc_tb), str(exc_type)

