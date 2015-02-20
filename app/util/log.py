import logging, os

LEVELS = {
    "urllib3": logging.WARN,
    "requests": logging.WARN,
}

FORMAT = "[%(levelname)s] %(asctime)s - %(name)s:%(lineno)d - %(message)s"

def set_logging_levels():
    for log, lvl in LEVELS.items():
        logging.getLogger(log).setLevel(lvl)

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    set_logging_levels()

    if os.path.exists("/var/log/emporium"):
        file_handler = logging.FileHandler('/var/log/emporium/app.log')
    else:
        file_handler = logging.FileHandler('/tmp/emporium.log')

    file_handler.setFormatter(logging.Formatter(FORMAT))

    root = logging.getLogger()
    root.addHandler(file_handler)

