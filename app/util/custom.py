import psycopg2
from psycopg2.extras import Json

# TODO: find a better spot
class SteamItem(object):
    def __init__(self, item_id, class_id, instance_id, item_meta={}):
        self.item_id = item_id
        self.class_id = class_id
        self.instance_id = instance_id
        self.item_meta = item_meta

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "class_id": self.class_id,
            "instance_id": self.instance_id,
            "item_meta": self.item_meta
        }

    def to_string(self):
        return "%s_%s" % (self.class_id, self.instance_id)

class SteamItemAdapter:
    def __init__(self, obj):
        self.adapted = psycopg2.extensions.SQL_IN((obj.item_id, obj.class_id, obj.instance_id, Json(obj.item_meta)))

    def prepare(self, conn):
        self.adapted.prepare(conn)

    def getquoted(self):
        return self.adapted.getquoted() + "::steam_item"

class SteamItemComposite(psycopg2.extras.CompositeCaster):
    def make(self, values):
        return SteamItem(*values)

def bind_custom_types(db):
    psycopg2.extras.register_composite('steam_item', db, factory=SteamItemComposite)

psycopg2.extensions.register_adapter(SteamItem, SteamItemAdapter)
