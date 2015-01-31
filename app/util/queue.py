import json, uuid, logging, time, thread

from emporium import steam
from database import redis
from util.push import WebPush

log = logging.getLogger(__name__)

FIVE_MINUTES = 60 * 5

def handle_inventory_jobs(job):
    inv_key = 'inv:%s' % job['steamid']

    if redis.exists(inv_key):
        result = {"success": True, "inventory": json.loads(redis.get(inv_key)), "type": "inventory"}
        log.debug('inventory job hit cache')
    else:
        try:
            log.debug('inventory job missed cache')
            inv = steam.market(730).get_inventory(job["steamid"])
            redis.set(inv_key, json.dumps(inv))
            result = {"success": True, "inventory": inv, "type": "inventory"}
        except:
            log.exception("Failed to process job %s")
            result = {"success": False, "inventory": {}, "type": "inventory"}

    WebPush(job['user']).send(result)

class JobQueue(object):
    def __init__(self, name, handler=None):
        self.name = name
        self.handler = handler
        self.channel = "jobq:%s" % self.name

    def fire(self, job_data):
        job_id = str(uuid.uuid4())
        data = json.dumps({
            "id": job_id, "data": job_data
        })

        log.info("Queueing job #%s" % job_id)
        redis.rpush("jobq:%s" % self.name, data)

    def process(self, id, data):
        start = time.time()
        self.handler(data)
        log.info("Finished job #%s (%s) in %ss" % (id, self.name, (time.time() - start)))

QUEUES = [
    ("inventory", handle_inventory_jobs)
]

def start_queues():
    queues = {
        i.channel: i for i in map(lambda i: JobQueue(*i), QUEUES)
    }

    while True:
        chan, data = redis.blpop(queues.keys())
        data = json.loads(data)

        log.info("Processing job #%s" % data['id'])
        thread.start_new_thread(queues[chan].process, (data['id'], data['data']))

