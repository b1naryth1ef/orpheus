from scheduler import Scheduler

from tasks.fraud_finder import run_fraud_check
from tasks.alerts import run_alert_checks

sched = Scheduler()

sched.add_task(run_fraud_check, minutes=60)
sched.add_task(run_alert_checks, minutes=1)

