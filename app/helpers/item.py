import logging
from util import create_enum

log = logging.getLogger(__name__)

ItemState = create_enum('UNKNOWN', 'EXTERNAL', 'INTERNAL', 'LOCKED')

