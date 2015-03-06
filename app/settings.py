import socket, os, json

from util.secure import SecureLoader

ENV = os.getenv("ENV", "LOCAL")
HOST = socket.gethostname().lower()
TESTING = os.getenv("TESTING")

# A list of email to send alert emails too
ALERT_EMAILS = ["b1naryth1ef@gmail.com"]

try:
    SECRET = json.load(open("/etc/secret.json", "r"))
except:
    print "Invalid Secret File. Does /etc/secret.json exist?"
    raise

# Postgres connection information
PG_HOST = "localhost"
PG_PORT = 5432
PG_USERNAME = "fort"
PG_DATABASE = "fort"
PG_PASSWORD = "fort"

# Redis connection information
R_HOST = "localhost"
R_PORT = 6379
R_DB = 0

if TESTING:
    PG_DATABASE = PG_USERNAME = "fort_test"
    PG_PASSWORD = "test"
    R_DB = 2

if ENV == "PROD":
    PG_PASSWORD = SECRET['postgres_password']

MANDRILL_API_KEY = SECRET.get("mandrill_key")
STEAM_API_KEY = SECRET.get("steamapi_key")

SECRET_KEY = SECRET.get("secret_key")

