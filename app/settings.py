from util.secure import SecureLoader
import socket

HOST = socket.gethostname().lower()

if HOST in ["csgoemporiumbackend"]:
    PG_HOST = "104.171.118.100"
    PG_PORT = 50432
    R_HOST = "104.171.118.100"
    R_PORT = 6379
else:
    PG_HOST = "localhost"
    PG_PORT = 5432
    R_HOST = "localhost"
    R_PORT = 6379

STEAM_API_KEY = 'D604C14A938F3DA1B8925C6FCB6A6A69'
SECRET_KEY = '\xfb\xcc\xe1\x1e\xae\x8aJ+\xe9\xbfm\xe7\x1e\xd3{f(\x1a\x97\xa1*l\xb9\xc8\x96\x10\xc3\x80\xc4\x93\xf5\x99'

# Eventually we will change this
CRYPT_KEY = 'Uu9_noCYmf1Bsa_KJH9K7fLdyQevUcyTk_RH8bhzHkY='
CRYPT = SecureLoader().load(CRYPT_KEY)

