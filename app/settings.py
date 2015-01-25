import socket, os

from util.secure import SecureLoader

ENV = os.getenv("ENV", "LOCAL")
HOST = socket.gethostname().lower()
TESTING = os.getenv("TESTING")

# Eventually we will change this
CRYPT_KEY = 'Uu9_noCYmf1Bsa_KJH9K7fLdyQevUcyTk_RH8bhzHkY='
CRYPT = SecureLoader().load(CRYPT_KEY)

PG_HOST = "localhost"
PG_PORT = 5432
PG_USERNAME = "emporium"
PG_DATABASE = "emporium"
PG_PASSWORD = CRYPT.get("postgres")
R_HOST = "localhost"
R_PORT = 6379
R_DB = 0

if TESTING:
    PG_DATABASE = PG_USERNAME = "emporium_test"
    PG_PASSWORD = "test"
    R_DB = 10

if ENV == "DEV":
    PG_DATABASE = PG_USERNAME = "emporium_dev"
    PG_PASSWORD = "dev"
    R_DB = 1

if ENV in ["PROD", "DEV"]:
    PG_HOST = "104.171.118.100"
    PG_PORT = 50432
    R_HOST = "104.171.118.100"

STEAM_API_KEY = 'D604C14A938F3DA1B8925C6FCB6A6A69'
SECRET_KEY = '\xfb\xcc\xe1\x1e\xae\x8aJ+\xe9\xbfm\xe7\x1e\xd3{f(\x1a\x97\xa1*l\xb9\xc8\x96\x10\xc3\x80\xc4\x93\xf5\x99'

