from scheduler import Scheduler

from tasks.fraud_finder import run_fraud_check

sched = Scheduler()

sched.add_task(run_fraud_check, minutes=60)

