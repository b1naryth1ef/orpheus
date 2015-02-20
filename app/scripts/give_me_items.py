#!/usr/bin/env python

import argparse, sys, os, json
sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), ".."))

from database import Cursor, redis

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", help="Steam ID of the user to send items too", required=True)
parser.add_argument("-t", "--token", help="The Steam trade token for the user")
parser.add_argument("-i", "--items", help="Comma or space seperated list of items too send", required=True)
args = parser.parse_args()


ADD_TRADE = """
INSERT INTO trades (state, ttype, token, to_id, message, items_in, items_out)
VALUES ('NEW', 'BET', %s, %s, 'give_me_items script', %s, %s)
RETURNING id;
"""

def main():
    if ',' in args.items:
        items = args.items.split(",")
    else:
        items = args.items.split(" ")

    with Cursor() as c:
        count = c.execute("SELECT count(*) as c FROM items WHERE id IN %s", (tuple(items), )).fetchone().c

        if count != len(items):
            print "ERROR: Invalid items"
            sys.exit(1)

        id = c.execute(ADD_TRADE, (args.token or '', args.user, [], map(int, items))).fetchone().id
        redis.rpush("trade-queue", json.dumps({"id": id}))

if __name__ == "__main__":
    main()

