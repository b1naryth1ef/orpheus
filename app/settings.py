import socket, os

from util.secure import SecureLoader

ENV = os.getenv("ENV", "LOCAL")
HOST = socket.gethostname().lower()
TESTING = os.getenv("TESTING")

# A list of email to send alert emails too
ALERT_EMAILS = ["b1naryth1ef@gmail.com"]

# Eventually we will change this
CRYPT_KEY = 'Uu9_noCYmf1Bsa_KJH9K7fLdyQevUcyTk_RH8bhzHkY='
CRYPT = SecureLoader().load(CRYPT_KEY)

# Postgres connection information
PG_HOST = "localhost"
PG_PORT = 5432
PG_USERNAME = "fort"
PG_DATABASE = "fort"
PG_PASSWORD = CRYPT.get("postgres")

# Redis connection information
R_HOST = "localhost"
R_PORT = 6379
R_DB = 0

if TESTING:
    PG_DATABASE = PG_USERNAME = "fort_test"
    PG_PASSWORD = "test"
    R_DB = 2

if ENV == "DEV":
    PG_PASSWORD = "dev"

if ENV in ["PROD", "DEV"]:
    PG_PORT = 5433

MANDRILL_API_KEY = CRYPT.get("mandrill")
STEAM_API_KEY = CRYPT.get("steam")

SECRET_KEY = '\xfb\xcc\xe1\x1e\xae\x8aJ+\xe9\xbfm\xe7\x1e\xd3{f(\x1a\x97\xa1*l\xb9\xc8\x96\x10\xc3\x80\xc4\x93\xf5\x99'

