import json, logging, socket, time

from dateutil.relativedelta import relativedelta
from datetime import datetime

from fort import steam
from database import redis, Cursor
from tasks import task

from util.steam import InvalidInventoryException, SteamAPIError
from tasks.inventory import update_item

log = logging.getLogger(__name__)
market = steam.market(730)

STEAM_SERVERS = {}

STEAM_SERVERS['SEATTLE'] = [
    "72.165.61.174:27017",
    "72.165.61.174:27018",
    "72.165.61.175:27017",
    "72.165.61.175:27018",
    "72.165.61.176:27017",
    "72.165.61.176:27018",
    "72.165.61.185:27017",
    "72.165.61.185:27018",
    "72.165.61.187:27017",
    "72.165.61.187:27018",
    "72.165.61.188:27017",
    "72.165.61.188:27018",
    '208.64.200.201:27017',
    '208.64.200.201:27018',
    '208.64.200.201:27019',
    '208.64.200.201:27020',
    '208.64.200.202:27017',
    '208.64.200.202:27018',
    '208.64.200.202:27019',
    '208.64.200.203:27017',
    '208.64.200.203:27018',
    '208.64.200.203:27019',
    '208.64.200.204:27017',
    '208.64.200.204:27018',
    '208.64.200.204:27019',
    '208.64.200.205:27017',
    '208.64.200.205:27018',
    '208.64.200.205:27019',
]

STEAM_SERVERS['ARIZONA'] = [
    "209.197.29.196:27017",
    "209.197.29.197:27017",
]

STEAM_SERVERS['LUXEMBOURG'] = [
    "146.66.152.12:27017",
    "146.66.152.12:27018",
    "146.66.152.12:27019",
    "146.66.152.13:27017",
    "146.66.152.13:27018",
    "146.66.152.13:27019",
    "146.66.152.14:27017",
    "146.66.152.14:27018",
    "146.66.152.14:27019",
    "146.66.152.15:27017",
    "146.66.152.15:27018",
    "146.66.152.15:27019",
]

STEAM_SERVERS['SINGAPORE'] = [
    "103.28.54.10:27017",
    "103.28.54.11:27017",
]

STEAM_SERVERS['WASHINGTON'] = [
    '208.78.164.9:27017',
    '208.78.164.9:27018',
    '208.78.164.9:27019',
    '208.78.164.10:27017',
    '208.78.164.10:27018',
    '208.78.164.10:27019',
    '208.78.164.11:27017',
    '208.78.164.11:27018',
    '208.78.164.11:27019',
    '208.78.164.12:27017',
    '208.78.164.12:27018',
    '208.78.164.12:27019',
    '208.78.164.13:27017',
    '208.78.164.13:27018',
    '208.78.164.13:27019',
    '208.78.164.14:27017',
    '208.78.164.14:27018',
    '208.78.164.14:27019'
]


@task()
def check_single_queue(qid):
    entry = redis.lrange(qid, -1, -1)
    if not len(entry):
        return

    entry = entry[0]
    data = json.loads(entry)

    with Cursor() as c:
        trade = c.execute("SELECT state, created_at FROM trades WHERE id=%s", (data['id'], )).fetchone()

        if not trade:
            log.warning("Trade %s doesn't exist. Wat?" % data['id'])
            return

        five_minutes_ago = datetime.utcnow() - relativedelta(minutes=5)
        if trade.created_at < five_minutes_ago:
            log.warning("Queue %s is backed up. Flushing..." % qid)

            # We'll let these trades naturally die
            # TODO: would be qewl to requeue these
            redis.delete(qid)
            return

@task()
def run_find_stuck_trades():
    map(check_single_queue, redis.keys("bot:*:tradeq"))

@task()
def test_steam_server(host):
    try:
        ip, port = host.split(":")
        socket.create_connection((ip, int(port)), 5).close()
        log.info("Steam server '%s' is up and responding!", host)
        redis.sadd("steamservers", host)
    except socket.error:
        log.warning("Steam server '%s' is down!", host)
        redis.srem("steamservers", host)

@task()
def check_steam_servers():
    for region, servers in STEAM_SERVERS.items():
        for server in servers:
            test_steam_server.queue(server)
            time.sleep(2)

@task(max_running=2, buffer_time=10)
def refresh_bot_inventory(id, steamid):
    log.info("Refreshing inventory for bot #%s", id)
    with Cursor() as c:
        try:
            inv = market.get_inventory(steamid)
        except InvalidInventoryException:
            log.error("Invalid Inventory for bot #%s", id)
            c.update("bots", id, inventory=[])
            return
        except SteamAPIError:
            log.error("Failed to get inventory for bot #%s", id)
            return

        # Blank the inventory out
        if not len(inv['rgInventory']):
            items = c.select("bots", "inventory", id=id).fetchone().inventory

            if len(items):
                c.execute("UPDATE items SET owner=NULL, state='EXTERNAL' WHERE id IN %s",
                    (tuple(items), ))

            c.update("bots", id, inventory=[])
            return

        items = set()
        for item_id, item in inv['rgInventory'].iteritems():
            ikey = "%s_%s" % (item['classid'], item['instanceid'])
            items.add(int(update_item(steamid, item_id, data=inv['rgDescriptions'][ikey])))

        c.execute("UPDATE items SET owner=%s, state='INTERNAL' WHERE id IN %s",
            (steamid, tuple(items)))
        c.update("bots", id, inventory=list(items))

@task()
def refresh_all_inventories():
    with Cursor() as c:
        bots = c.execute("SELECT id, steamid FROM bots WHERE status IN ('AVAIL', 'USED')"
            ).fetchall(as_list=True)

    for bot in bots:
        refresh_bot_inventory(bot.id, bot.steamid)

