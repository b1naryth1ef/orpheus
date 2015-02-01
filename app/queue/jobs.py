import json, logging

from emporium import steam
from database import redis, Cursor

from util.push import WebPush
from util.steam import SteamAPIError

FIVE_MINUTES = 60 * 5

log = logging.getLogger(__name__)

def process_item(name, image, data):
    with Cursor() as c:
        pdata = c.execute("SELECT id, price FROM items WHERE name=%s", (name, )).fetchone()

        if pdata:
            return (pdata.id, float(pdata.price))

        try:
            i_vol, i_low, i_med = steam.market(730).get_item_price(name)
        except SteamAPIError:
            log.exception("Failed to get price for item '%s'" % name)

        new = c.execute("INSERT INTO items (name, price, meta) VALUES (%s, %s, %s) RETURNING id", (
            name, i_low, Cursor.json({
                "image": image,
                "descriptions": data
            })
        )).fetchone()
        return (new.id, i_low)

def process_inventory(data):
    inv = []

    for item_id, item in data['rgInventory'].iteritems():
        key = item['classid'] + "_" + item['instanceid']
        obj = data['rgDescriptions'][key]

        if not obj.get('tradable') or not 'icon_url_large' in obj:
            continue

        item_name = obj['market_hash_name']
        item_image = obj['icon_url_large']
        id, price = process_item(item_name, item_image, obj.get('descriptions', []))

        inv.append({
            "id": id,
            "price": price,
            "image": item_image
        })

    return inv

def handle_inventory_job(job):
    inv_key = 'inv:%s' % job['steamid']

    if redis.exists(inv_key):
        result = {"success": True, "inventory": json.loads(redis.get(inv_key)), "type": "inventory"}
        return WebPush(job['user']).send(result)

    try:
        inv = steam.market(730).get_inventory(job["steamid"])
        inv = process_inventory(inv)
        redis.set(inv_key, json.dumps(inv))
        result = {"success": True, "inventory": inv, "type": "inventory"}
    except SteamAPIError:
        log.exception("Failed to load inventory:")
        result = {"success": False, "inventory": {}, "type": "inventory"}

    WebPush(job['user']).send(result)

