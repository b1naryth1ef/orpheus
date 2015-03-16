import json, uuid, logging, thread, time, os

from database import redis

log = logging.getLogger(__name__)

TASKS = {}

def task(*args, **kwargs):
    def deco(f):
        task = Task(f.__name__, f, *args, **kwargs)

        if f.__name__ in TASKS:
            raise Exception("Conflicting task name: %s" % f.__name__)

        TASKS[f.__name__] = task
        return task
    return deco

class Task(object):
    def __init__(self, name, f, max_running=None, buffer_time=None):
        self.name = name
        self.f = f
        self.max_running = max_running
        self.buffer_time = buffer_time

    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)

    def queue(self, *args, **kwargs):
        id = str(uuid.uuid4())
        redis.rpush("jq:%s" % self.name, json.dumps({
            "id": id,
            "args": args,
            "kwargs": kwargs
        }))
        return id

class TaskRunner(object):
    def __init__(self, name, task):
        self.name = name
        self.f = task
        self.running = 0

    def process(self, job):
        self.running += 1
        log.info('[%s] Running job %s...', job['id'], self.name)
        redis.set("task:%s" % job['id'], 1)
        start = time.time()

        try:
            self.f(*job['args'], **job['kwargs'])
            if self.f.buffer_time:
                time.sleep(self.f.buffer_time)
        except:
            log.exception("[%s] Failed in %ss", job['id'], time.time() - start)
        finally:
            redis.delete("task:%s" % job['id'])
            self.running -= 1
        log.info('[%s] Completed in %ss', job['id'], time.time() - start)

    def run(self, job):
        if self.f.max_running:
            while self.f.max_running <= self.running:
                time.sleep(.5)

        thread.start_new_thread(self.process, (job, ))

class TaskManager(object):
    def __init__(self):
        self.load()
        self.queues = ["jq:" + i for i in TASKS.keys()]
        self.runners = {k: TaskRunner(k, v) for k, v in TASKS.items()}
        self.active = True

    def load(self):
        for f in os.listdir("tasks/"):
            if f.endswith(".py"):
                __import__("tasks." + f.rsplit(".")[0])

    def run(self):
        log.info("Running TaskManager on %s queues...", len(self.queues))
        while self.active:
            chan, job = redis.blpop(self.queues)
            job_name = chan.split(":", 1)[1]
            job = json.loads(job)

            if job_name not in TASKS:
                log.error("Cannot handle task %s",job_name)
                continue

            self.runners[job_name].run(job)

