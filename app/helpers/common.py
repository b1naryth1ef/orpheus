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

    content = ''.join(traceback.format_exception(exc_type, exc_obj, exc_tb))

    with Cursor() as c:
        c.execute(CREATE_EXCEPTION_SQL, (
            id, str(exc_type), content, Cursor.json(meta),
            datetime.utcnow()))

    return id

def get_enum_array(enum_type):
    enum_values = {}
    
    with Cursor() as c:
        c.execute("SELECT unnest(enum_range(NULL::{0}))".format(enum_type))
        
        for entry in c.fetchall():
            enum_values[entry.unnest] = entry.unnest
        
    return enum_values
    