"""
TODO:
    - remove peewee
    - unittests plzzzzz
    - create function to aggregate/load data from schema
    - figure out how to do multiple drafts for different games
    - figure out how to store drafts
    - figure out how to draft both possible results at the SAME DAMN TIME
    - make it fasterified plz
"""

import time
from peewee import *

db = PostgresqlDatabase("emporium_draft", user="emporium", password="1")

class Better(Model):
    class Meta:
        database = db
        indexes = (
            (('id', ), True),
            (('need', ), False),
            (('current', ), False)
        )

    id = IntegerField(primary_key=True)
    need = FloatField()
    current = FloatField(default=0)

class Item(Model):
    class Meta:
        database = db

    indexes = (
        (('id', ), True),
        (('value'), False),
        (('better'), False)
    )

    id = IntegerField(primary_key=True)
    value = FloatField()
    better = ForeignKeyField(Better, null=True)

Item.drop_table(True)
Better.drop_table(True)
Better.create_table()
Item.create_table()

def pre_draft(betters, items):
    with db.transaction():
        print "Inserting betters..."
        for (id, need) in betters:
            Better.create(id=id, need=need)

        print "Inserting items..."
        for (id, value) in items:
            Item.create(id=id, value=value)


def run_draft():
    for i, item in enumerate(Item.select().where(Item.better == None)):
        if not i % 100:
            print "Handling item %s" % i
        draft_item(item)

def draft_item(item):
    c = db.get_cursor()

    # This is slow, but super accurate
    # approx 35 items a second
    QUERY = """
    SELECT better.*, count(item.better_id) as num_items
    FROM better LEFT JOIN item ON (better.id = item.better_id)
    WHERE better.current <= %s
    GROUP BY better.id ORDER BY num_items, need DESC LIMIT 1
    """

    # This is hella fast, but is greedy (making it somewhat inaccurate)
    # approx 300 items a second
    QUERY_2 = """
    SELECT better.* FROM better
    WHERE better.current <= %s
    ORDER BY need DESC LIMIT 1
    """

    c.execute(QUERY_2 % item.value)

    entry = c.fetchone()
    item.better = entry[0]
    item.save()

    c.execute("UPDATE better SET current=%s WHERE id=%s" % ((entry[2] + item.value), entry[0]))
    db.commit()

if __name__ == "__main__":
    import random, time, sys

    # 25,000 people placed 250,000 items for bet

    low_bins = map(lambda i: (i, random.randint(3, 500) / 100), range(1, 15000))
    med_bins = map(lambda i: (i + 15000, random.randint(5, 25)), range(1, 10000))
    high_bins = map(lambda i: (i + 25000, random.randint(25, 900)), range(1, 5000))
    all_bins = low_bins + med_bins + high_bins

    low_items = map(lambda i: (i, random.randint(3, 500) / 100), range(1, 150000))
    med_items = map(lambda i: (i + 150000, random.randint(5, 20)), range(1, 50000))
    high_items = map(lambda i: (i + 200000, random.randint(20, 300)), range(1, 50000))
    all_items = low_items + med_items + high_items

    if sum(map(lambda i: i[1], all_bins)) > sum(map(lambda i: i[1], all_items)):
        print "Won't work with random data..."
        sys.exit(1)

    start = time.time()
    pre_draft(all_bins, all_items)
    print "Pre-draft took %ss" % (time.time() - start)

    start = time.time()
    run_draft()
    print "Draft Took %ss" % (time.time() - start)
    """
    item_weights = map(lambda i: i.weight, leftover_items)
    bin_weights = map(lambda i: i.current_weight(), sorted_bins)
    print "%s leftovers" % len(leftover_items)
    print "Most value stolen: %s" % max(bin_weights)
    print "Average value stolen: %s" % (sum(bin_weights) / len(bin_weights))
    print "Max leftover item: %s" % max(item_weights)
    print "Min leftover item: %s" % min(item_weights)
    """

