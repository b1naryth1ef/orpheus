#!/usr/bin/env python
import os, sys, getpass, argparse, psycopg2, redis, time

DIR = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()

parser.add_argument("-F", "--flushall", help="Flush all tables and data", action="store_true")
parser.add_argument("-C", "--create", help="Create all unknown tables", action="store_true")
parser.add_argument("-G", "--generate", help="Generate test data", action="store_true")
parser.add_argument("-M", "--migrate", help="Run any required migrations", action="store_true")
parser.add_argument("-a", "--addmigration", help="Create a new empty migration", action="store_true")

parser.add_argument("-u", "--username", help="PSQL Username", default="fort")
parser.add_argument("-H", "--host", help="PSQL Host", default="localhost")
parser.add_argument("-d", "--database", help="PSQL DB", default="fort")
parser.add_argument("-p", "--port", help="PSQL Port", default="5432")

args = parser.parse_args()

# Lists all the tables in a database
LIST_TABLES_SQL = """
SELECT table_name
  FROM information_schema.tables
   WHERE table_schema='public'
      AND table_type='BASE TABLE';
"""

# Lists all the custom types in a schema/database
LIST_TYPES_SQL = """
SELECT      n.nspname as schema, t.typname as type
FROM        pg_type t
LEFT JOIN   pg_catalog.pg_namespace n ON n.oid = t.typnamespace
WHERE       (t.typrelid = 0 OR (SELECT c.relkind = 'c' FROM pg_catalog.pg_class c WHERE c.oid = t.typrelid))
AND     NOT EXISTS(SELECT 1 FROM pg_catalog.pg_type el WHERE el.oid = t.typelem AND el.typarray = t.oid)
AND     n.nspname NOT IN ('pg_catalog', 'information_schema')
"""

MIGRATION_TEMPLATE = open("data/template.py", "r").read()

def open_database_connection(pw, db):
    return psycopg2.connect("host={host} port={port} dbname={db} user={user} password='{pw}'".format(
        host=args.host,
        user=args.username,
        db=db,
        pw=pw,
        port=int(args.port)))

def add_migration():
    migrations = set(os.listdir("migrations"))
    id = str(int(max(migrations)) + 1).zfill(4)
    print "Creating migration #%s" % id

    os.mkdir("migrations/%s" % id)

    with open("migrations/%s/migrate.py" % id, "w") as f:
        f.write(MIGRATION_TEMPLATE.format(num=id, date=time.time()))

    print "  DONE"
    sys.exit(0)

def run_migrations(db):
    c = db.cursor()
    c.execute("SELECT max(version) FROM schemaversion")
    current = c.fetchone()[0]
    c.close()

    new_migrations = filter(lambda i: int(i) > current, os.listdir("migrations"))

    if not len(new_migrations):
        print "No migrations to run"
        return 1

    print "Running %s migrations..." % len(new_migrations)

    for migration in new_migrations:
        migration_path = os.path.join(DIR, "migrations", migration)
        print "  running migration %s..." % migration

        if not os.path.exists(os.path.join(migration_path, "migrate.py")):
            print "  ERROR: No migrate.py for migration, cannot run!"

        code = {}
        exec open(os.path.join(migration_path, "migrate.py"), "r").read() in code

        print "  running pre-migration..."
        if code["before"](db) is False:
            print "  ERROR: pre-migration failed!"
            return sys.exit(1)

        print "  running migration..."
        if code["during"](db) is False:
            print "  ERROR: migration failed!"
            return sys.exit(1)

        print "  running post-migration..."
        if code["after"](db) is False:
            print "  ERROR: post-migration failed!"
            return sys.exit(1)

        c = db.cursor()
        c.execute("INSERT INTO schemaversion VALUES (%s)", (int(migration), ))
        db.commit()
        print "  migration %s finished" % migration

    print "Finished running migrations"

def main():
    if not any((args.flushall, args.create, args.generate, args.migrate, args.addmigration)):
        parser.print_help()
        sys.exit(1)

    if args.addmigration:
        sys.exit(add_migration())

    password = getpass.getpass("DB Password > ")
    db = open_database_connection(password, args.database)
    draft_db = open_database_connection(password, args.database + "_draft")
    db.autocommit = True
    draft_db.autocommit = True
    is_prod_db = args.database == "fort"

    if args.flushall:
        print "Flushing all tables and types..."
        if is_prod_db and raw_input("You are about to drop everything in production. Are you sure? ").lower()[0] != 'y':
            print "ERROR: Yeah right! Please confirm before dropping all tables!"
            return sys.exit(1)

        cursor = db.cursor()
        cursor.execute(LIST_TABLES_SQL)
        for table in cursor.fetchall():
            print "  Dropping table '%s'" % table[0]
            cursor.execute("DROP TABLE %s CASCADE" % table[0])

        cursor.execute(LIST_TYPES_SQL)
        for ctype in cursor.fetchall():
            print "  Dropping type '%s'" % ctype[1]
            cursor.execute("DROP TYPE %s" % ctype[1])

        cursor = draft_db.cursor()
        cursor.execute(LIST_TABLES_SQL)
        for table in cursor.fetchall():
            print "  Dropping draft table '%s'" % table[0]
            cursor.execute("DROP TABLE %s CASCADE" % table[0])

        print "  Flushing redis..."
        redis.Redis().flushall()

        print "  DONE!"

    if args.create:
        print "Creating all tables..."
        with open(os.path.join(DIR, "schema.sql"), "r") as f:
            cursor = db.cursor()
            cursor.execute(f.read())

        with open(os.path.join(DIR, "data/draft_schema.sql"), "r") as f:
            cursor = draft_db.cursor()
            cursor.execute(f.read())

        print "  Conforming table ownership..."
        with db.cursor() as c:
            c.execute(LIST_TABLES_SQL)
            for table in c.fetchall():
                c.execute("ALTER TABLE %s OWNER TO %s" % (table[0], 'fort'))

            c.execute(LIST_TYPES_SQL)
            for ttype in c.fetchall():
                c.execute("ALTER TYPE %s OWNER TO %s" % (ttype[1], 'fort'))

        print "  DONE!"

    if args.generate:
        print "Generating fake data..."
        from generate import DATA_GENERATORS

        with db.cursor() as c:
            for gen in DATA_GENERATORS:
                print "  running %s" % gen.__name__
                gen(c, db)
        
        print "  DONE!"

    if args.migrate:
        sys.exit(run_migrations(db))

main()

