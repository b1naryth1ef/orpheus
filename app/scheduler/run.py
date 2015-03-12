from scheduler import Scheduler

from tasks.fraud_finder import run_fraud_check
from tasks.alerts import run_alert_checks
from tasks.itemdraft import create_item_drafts, run_item_drafts
from tasks.bots import run_find_stuck_trades
from tasks.returns import distribute_returns, apply_draft_items
from tasks.inventory import update_item_images, backfill_item_types, update_prices

sched = Scheduler()

sched.add_task(run_fraud_check, minutes=60)
sched.add_task(run_alert_checks, seconds=10, start_now=True)

sched.add_task(create_item_drafts, minutes=2, start_now=True)
sched.add_task(run_item_drafts, minutes=2, start_now=True)
sched.add_task(run_find_stuck_trades, minutes=2, start_now=True)
sched.add_task(apply_draft_items, minutes=2, start_now=True)
sched.add_task(distribute_returns, minutes=2, start_now=True)

# Item Tasks
sched.add_task(update_item_images, minutes=15, start_now=True)
sched.add_task(backfill_item_types, minutes=2, start_now=True)
# sched.add_task(update_prices, ...)

