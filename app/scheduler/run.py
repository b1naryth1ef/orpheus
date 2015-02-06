from scheduler import Scheduler

from tasks.fraud_finder import run_fraud_check
from tasks.alerts import run_alert_checks
from tasks.bets import run_find_stuck_bets
from tasks.itemdraft import run_item_drafts

sched = Scheduler()

sched.add_task(run_fraud_check, minutes=60)
sched.add_task(run_alert_checks, seconds=10, start_now=True)
sched.add_task(run_find_stuck_bets, days=2, start_now=True)
sched.add_task(run_item_drafts, minutes=2, start_now=True)
