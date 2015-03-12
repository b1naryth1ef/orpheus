import logging

from fort import steam
from database import Cursor

log = logging.getLogger(__name__)

ITEM_IMAGES_QUERY = """
SELECT id, class_id, instance_id FROM items WHERE image IS NULL AND state != 'UNKNOWN'
"""

def update_item_images():
    market = steam.market(730)
    with Cursor() as c:
        c.execute(ITEM_IMAGES_QUERY)

        for item in c.fetchall():
            data = market.get_asset_class_info(item.class_id, item.instance_id)
            c.execute("UPDATE items SET image=%s WHERE id=%s", (item.id, data['icon_url_large']))

def update_prices():
    pass

BACKFILL_TYPES_QUERY = """
SELECT i.id, i.class_id, i.instance_id FROM items i
LEFT JOIN itemtypes it ON it.id=i.type_id
WHERE it.id IS NULL;
"""

def backfill_item_types():
    market = steam.market(730)

    with Cursor() as c:
        c.execute(BACKFILL_TYPES_QUERY)

        for item in c.fetchall(as_list=True):
            data = market.get_asset_class_info(item.class_id, item.instance_id)

            item_type = c.execute("SELECT id FROM itemtypes WHERE name=%s",
                (data['name'], )).fetchone()

            if not item_type:
                id = c.insert("itemtypes", {
                    "name": data['name']
                })
            else:
                id = item_type.id

            c.execute("UPDATE items SET type_id=%s WHERE id=%s", (id, item.id))

