#!/usr/bin/env python
from cryptography.fernet import Fernet
import json, sys, getpass, argparse

class SecureLoader(object):
    def __init__(self, location="/etc/secret.json"):
        self.location = location

        self.f = open(self.location, "r+")

    def load(self, master_key):
        d = Fernet(master_key)
        data = self.f.read()
        if not data:
            return {}
        return json.loads(d.decrypt(data))

    def dump(self, master_key, data):
        d = Fernet(master_key)
        self.f.seek(0)
        self.f.write(d.encrypt(json.dumps(data)))
        self.f.truncate()
        self.f.flush()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--decrypt", help="Decrypt a secure entry", action="store_true")
    parser.add_argument("-e", "--encrypt", help="Encrypt and add a secure entry", action="store_true")
    parser.add_argument("-r", "--remove", help="Remove a secure entry", action="store_true")
    parser.add_argument("-n", "--name", help="Entry name", required=True)
    parser.add_argument("-v", "--value", help="Value to be encrypted")
    args = parser.parse_args()

    if len([i for i in [args.decrypt, args.encrypt, args.remove] if i]) != 1:
        print args.decrypt, args.encrypt, args.remove
        parser.print_help()
        sys.exit(1)

    pw = getpass.getpass("Master Password > ")
    loader = SecureLoader()
    data = loader.load(pw)

    if args.decrypt:
        print data[args.name]
    elif args.encrypt:
        data[args.name] = args.value
    elif args.remove:
        del data[args.name]

    loader.dump(pw, data)
