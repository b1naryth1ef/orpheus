import json, logging, uuid

from emporium import steam
from database import redis, Cursor

from util.push import WebPush
from util.steam import SteamAPIError

from helpers.item import ItemState

FIVE_MINUTES = 60 * 5

log = logging.getLogger(__name__)

def process_item(name, image, data):
    with Cursor() as c:
        pdata = c.execute("SELECT id, price FROM itemtypes WHERE name=%s", (name, )).fetchone()

        if pdata:
            return (pdata.id, float(pdata.price))

        try:
            i_vol, i_low, i_med = steam.market(730).get_item_price(name)
        except SteamAPIError:
            log.exception("Failed to get price for item '%s'" % name)

        new = c.execute("INSERT INTO itemtypes (name, price, meta) VALUES (%s, %s, %s) RETURNING id", (
            name, i_low, Cursor.json({})
        )).fetchone()
        return (new.id, i_low)

def process_inventory(data, steamid):
    c = Cursor()
    inv = []

    if not isinstance(data['rgInventory'], dict):
        print data

    for item_id, item in data['rgInventory'].iteritems():
        key = item['classid'] + "_" + item['instanceid']
        obj = data['rgDescriptions'][key]

        if not obj.get('tradable') or not 'icon_url_large' in obj or not 'actions' in obj:
            continue

        """
        asset_id = filter(lambda i: i.get("name") == "Inspect in Game...", obj['actions'])
        if len(asset_id) != 1:
            continue

        # Try and hack out the assetid because steam sux
        asset_id = asset_id[0]['link'].rsplit("assetid%D", 1)[-1]
        if not asset_id.isdigit():
            log.warning("Got an assetid which is not an integer: %s", asset_id)
            continue
        """

        # Grab some general information
        item_name = obj['market_hash_name']
        item_image = obj['icon_url_large']
        type_id, price = process_item(item_name, item_image, obj.get('descriptions', []))

        # Make sure we have this item in the database, and it's not totally fuck-boner-fied
        existing_item = c.execute("SELECT state, owner FROM items WHERE id=%s", (item_id, )).fetchone()
        if existing_item:
            if existing_item.state != ItemState.EXTERNAL:
                if existing_item.state == ItemState.LOCKED:
                    log.error("Found itemid %s in inventory %s, but it's locked!" % (item_id, steamid))
                    continue

            if not existing_item.owner:
                log.debug("Updating owner for item %s" % item_id)
                c.execute("UPDATE items SET owner=%s WHERE id=%s", (steamid, item_id))
        else:
            c.execute("""
                INSERT INTO items (id, owner, type_id, class_id, instance_id, state, meta)
                VALUES (%(id)s, %(owner)s, %(type_id)s, %(class_id)s, %(instance_id)s, %(state)s, %(meta)s);
            """, {
                "id": item_id,
                "owner": steamid,
                "type_id": type_id,
                "class_id": item['classid'],
                "instance_id": item['instanceid'],
                "state": ItemState.EXTERNAL,
                "meta": c.json({
                    "desc": obj.get('descriptions', []),
                    "image": item_image
                })
            })

        # Overpriced items make us sad
        if price == 0:
            continue

        inv.append({
            "id": item_id,
            "type": type_id,
            "price": price,
            "image": item_image
        })

    return inv

# TODO: fucking fix this shit
def get_pending_items(uid):
    return []
    with Cursor() as c:
        pending = c.execute("SELECT unnest(items) as items FROM bets WHERE better=%s AND state='offered'", (uid, )).fetchall()
        return map(lambda i: i.item_id, map(lambda i: i.items, pending))

def handle_inventory_job(job):
    inv_key = 'inv:%s' % job['steamid']

    if redis.exists(inv_key):
        inv = json.loads(redis.get(inv_key))
        pending = get_pending_items(job['user'])

        inv = filter(lambda i: (False and pending.remove(i['id'])) if i['id'] in pending else True, inv)

        result = {"success": True, "inventory": inv, "type": "inventory"}
        return WebPush(job['user']).send(result)

    try:
        inv = steam.market(730).get_inventory(job["steamid"])
        inv = process_inventory(inv, job["steamid"])
        redis.set(inv_key, json.dumps(inv))
        result = {"success": True, "inventory": inv, "type": "inventory"}
    except SteamAPIError:
        log.exception("Failed to load inventory:")
        result = {"success": False, "inventory": {}, "type": "inventory"}

    WebPush(job['user']).send(result)

def handle_bot_update_job(job):
    with Cursor() as c:
        steamid = c.execute("SELECT steamid FROM bots WHERE id=%s", (job['bot'], )).fetchone().steamid

        inv = steam.market(730).get_inventory(steamid)
        inv = process_inventory(inv, steamid)
        items = map(lambda i: int(i['id']), inv)
        c.execute("UPDATE bots SET inventory=%s WHERE id=%s", (items, job['bot']))

