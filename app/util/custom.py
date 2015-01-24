import psycopg2

# TODO: find a better spot
class SteamItem(object):
    def __init__(self, class_id, instance_id):
        self.class_id = class_id
        self.instance_id = instance_id

class SteamItemAdapter:
    def __init__(self, obj):
        self.adapted = psycopg2.extensions.SQL_IN((obj.class_id, obj.instance_id))

    def prepare(self, conn):
        self.adapted.prepare(conn)

    def getquoted(self):
        return self.adapted.getquoted() + "::steam_item"

psycopg2.extensions.register_adapter(SteamItem, SteamItemAdapter)
