import json, logging, uuid, time

from fort import steam
from database import redis, Cursor
from datetime import datetime

from util.push import WebPush
from util.steam import SteamAPIError

from helpers.item import ItemState

from tasks import task

FIVE_MINUTES = 60 * 5

log = logging.getLogger(__name__)
market = steam.market(730)

@task
def update_item(owner_id, item_id, class_id=None, instance_id=None, data=None):
    with Cursor() as c:
        data = data or market.get_asset_class_info(class_id, instance_id)

        item = c.execute("SELECT id FROM items WHERE id=%s", (item_id, )).fetchone()
        item_price = c.execute("SELECT price FROM itemprices WHERE name=%s",
            (data['market_hash_name'], )).fetchone()

        if not data['tradable'] or not data['marketable']:
            return -1

        actions = []
        if 'actions' in data:
            if not isinstance(data['actions'], list):
                actions = data['actions'].values()
            else:
                actions = data['actions']

        payload = {
            "owner": owner_id,
            "name": data['market_hash_name'],
            "class_id": data['classid'],
            "instance_id": data['instanceid'],
            "state": ItemState.EXTERNAL,
            "image": data.get("icon_url_large", data.get("icon_url")),
            "price": item_price.price if item_price else None,
            "meta": c.json({
                "desc": data.get('descriptions', []),
                "actions": actions,
                "color": data.get("name_color", "")
            })
        }

        if item:
            c.update("items", item_id, payload)
        else:
            payload['id'] = item_id
            c.insert("items", payload)

        # We queue a new job because this needs to be seperatly rate-limited
        if not item_price:
            update_item_price.queue(item_id)
        return item_id

@task
def update_item_price(item_id):
    with Cursor() as c:
        item = c.execute("""
            SELECT i.name, ip.id as pid FROM items i
            LEFT JOIN itemprices ip ON ip.name=i.name
            WHERE i.id=%s
        """, (item_id, )).fetchone()

        try:
            i_vol, i_low, i_med = market.get_item_price(item.name.decode('utf-8'))

            if item.pid:
                c.update("itemprices", item.pid, price=i_low, updated=datetime.utcnow())
            else:
                c.insert("itemprices", name=item.name, price=i_low, updated=datetime.utcnow())

            c.update("items", item_id, price=i_low)
        except SteamAPIError:
            log.exception("Failed to get price for item '%s'", item_id)

    return i_low

@task
def update_prices():
    pass

@task
def push_steam_inventory(user_id, changed=False):
    with Cursor() as c:
        if not redis.exists("u:%s:inv" % user_id):
            return load_steam_inventory.queue(user_id, push=True)

        items = c.execute("""
            SELECT id, name, image, price, meta FROM items
            WHERE id in %s AND price > 0
        """, (tuple(redis.smembers("u:%s:inv" % user_id)), )).fetchall()

        inv = []
        for item in items:
            if int(item.price) > 380 or float(item.price) < .05:
                continue

            inv.append({
                "id": str(item.id),
                "name": item.name,
                "image": item.image,
                "price": str(item.price),
                "meta": item.meta
            })

        # Lets refresh this
        load_steam_inventory.queue(user_id)
        return WebPush(user_id).send({
            "success": True,
            "inventory": inv,
            "type": "inventory",
            "new": changed
        })

@task
def load_steam_inventory(user_id, push=False, force=False):
    pipe = redis.pipeline(transaction=False)
    data = pipe.exists("u:%s:inv" % user_id).get("u:%s:inv:updated" % user_id).execute()
    last_update = time.time() - float(data[1] or 0)
    diff = False

    # We do this to avoid spamming steam API's but keeping things as up-to-date as possible
    if force or not data[1] or last_update > 300:
        with Cursor() as c:
            temp_key = "u:%s:inv" % str(uuid.uuid4())
            user = c.execute("SELECT steamid FROM users WHERE id=%s", (user_id, )).fetchone()
            data = steam.market(730).get_inventory(user.steamid)

            ids = []
            for item_id, item in data['rgInventory'].iteritems():
                ikey = "%s_%s" % (item['classid'], item['instanceid'])
                ids.append(update_item(user.steamid, item_id, data=data['rgDescriptions'][ikey]))

            # TODO: Pipeline this eventually
            pipe = redis.pipeline()
            pipe.sadd(temp_key, *filter(lambda i: i != -1, ids))
            pipe.sdiff("u:%s:inv" % user_id, temp_key)
            pipe.rename(temp_key, "u:%s:inv" % user_id)
            pipe.set("u:%s:inv:updated" % user_id, time.time())
            res = pipe.execute()

            diff = bool(len(res[1]))
    else:
        log.debug("Skipping inventory reload, still within cache time")

    if push:
        push_steam_inventory.queue(user_id, diff)

