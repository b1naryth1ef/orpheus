from scheduler import Scheduler

from tasks.itemdraft import create_item_drafts, run_item_drafts
from tasks.returns import distribute_returns, apply_draft_items

sched = Scheduler()

# Item Drafts
sched.schedule(create_item_drafts, minutes=2, start_now=True)
sched.schedule(run_item_drafts, minutes=2, start_now=True)

# Returns
sched.schedule(distribute_returns, minutes=2, start_now=True)
sched.schedule(apply_draft_items, seconds=30, start_now=True)

