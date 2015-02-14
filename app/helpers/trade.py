import logging
from datetime import datetime
from psycopg2.extras import Json

from emporium import steam
from database import Cursor
from util import create_enum

log = logging.getLogger(__name__)

TradeState = create_enum('NEW', 'IN-PROGRESS', 'OFFERED', 'ACCEPTED', 'REJECTED', 'UNKNOWN')
TradeType = create_enum('BET', 'RETURNS', 'INTERNAL')

