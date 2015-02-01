import logging
from datetime import datetime
from psycopg2.extras import Json

from emporium import steam
from database import Cursor
from util.errors import ValidationError
from helpers.user import UserGroup

log = logging.getLogger(__name__)

def ensure_item_added(name, class_id, instance_id, image):
    try:
        item_price = steam.market().get_item_price(name)
    except SteamAPIError:
        log.exception("Failed to get price for item '%s'" % name)

    with Cursor() as c:
        c.execute("SELECT id FROM items WHERE name=%s", (name, ))


