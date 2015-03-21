from scheduler import Scheduler

from tasks.itemdraft import create_item_drafts, run_item_drafts
from tasks.returns import distribute_returns, apply_draft_items
from tasks.bots import check_steam_servers
from tasks.trades import update_trades

sched = Scheduler()

# Item Drafts
sched.schedule(create_item_drafts, minutes=2, start_now=True)
sched.schedule(run_item_drafts, minutes=2, start_now=True)

# Returns
sched.schedule(distribute_returns, minutes=2, start_now=True)
sched.schedule(apply_draft_items, seconds=30, start_now=True)

# Bots
sched.schedule(check_steam_servers, minutes=25)

# Trades
sched.schedule(update_trades, seconds=45, start_now=True)
