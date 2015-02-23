import json, uuid, logging, time, thread

from emporium import steam
from database import redis

from jobs.inventory import handle_inventory_job, handle_bot_update_job

log = logging.getLogger(__name__)

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
    ("inventory", handle_inventory_job),
    ("botupdate", handle_bot_update_job),
]

def start_queues():
    queues = {
        i.channel: i for i in map(lambda i: JobQueue(*i), QUEUES)
    }

    log.info("Starting %s queues..." % len(QUEUES))

    while True:
        chan, data = redis.blpop(queues.keys())
        data = json.loads(data)

        log.info("Processing job #%s" % data['id'])
        thread.start_new_thread(queues[chan].process, (data['id'], data['data']))

