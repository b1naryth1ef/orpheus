from scheduler import Scheduler

from tasks.fraud_finder import run_fraud_check
from tasks.alerts import run_alert_checks
from tasks.itemdraft import create_item_drafts, run_item_drafts
from tasks.bots import run_find_stuck_trades
from tasks.returns import distribute_returns, apply_draft_items

sched = Scheduler()

sched.add_task(run_fraud_check, minutes=60)
sched.add_task(run_alert_checks, seconds=10, start_now=True)

sched.add_task(create_item_drafts, minutes=2, start_now=True)
sched.add_task(run_item_drafts, minutes=2, start_now=True)
sched.add_task(run_find_stuck_trades, minutes=2, start_now=True)
sched.add_task(apply_draft_items, minutes=2, start_now=True)
sched.add_task(distribute_returns, minutes=2, start_now=True)
