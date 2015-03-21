import logging

from tasks import task
from database import Cursor

log = logging.getLogger(__name__)

NEED_ITEM_LOCK = """
SELECT id FROM matches
WHERE state='OPEN' AND (match_date - interval '5 minutes') > now()
"""

@task()
def lock_match_items():
    with Cursor() as c:
        c.execute(NEED_ITEM_LOCK)

        for match in c.fetchall():
            log.info("Transitioning match #%s to locked", match.id)
            c.update("matches", match.id, state='WAITING', itemstate='LOCKED')

