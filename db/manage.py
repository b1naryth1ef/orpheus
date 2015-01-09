#!/usr/bin/env python
import os, sys, getpass, argparse, psycopg2

DIR = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dropall", help="Drop all databases before creating", action="store_true")
parser.add_argument("-c", "--create", help="Create all unknown tables", action="store_true")
parser.add_argument("-m", "--migration", help="Run a migration", action="store_true")
parser.add_argument("-u", "--username", help="PSQL Username", default="emporium")
parser.add_argument("-s", "--server", help="PSQL Host", default="localhost")
args = parser.parse_args()

LIST_TABLES_SQL = """
SELECT table_name
  FROM information_schema.tables
   WHERE table_schema='public'
      AND table_type='BASE TABLE';
"""

LIST_TYPES_SQL = """
SELECT      n.nspname as schema, t.typname as type
FROM        pg_type t
LEFT JOIN   pg_catalog.pg_namespace n ON n.oid = t.typnamespace
WHERE       (t.typrelid = 0 OR (SELECT c.relkind = 'c' FROM pg_catalog.pg_class c WHERE c.oid = t.typrelid))
AND     NOT EXISTS(SELECT 1 FROM pg_catalog.pg_type el WHERE el.oid = t.typelem AND el.typarray = t.oid)
AND     n.nspname NOT IN ('pg_catalog', 'information_schema')
"""

def open_database_connection(pw):
    return psycopg2.connect("host={host} port={port} dbname=emporium user={user} password={pw}".format(
        host=args.server,
        user=args.username,
        pw=pw,
        port=50432 if args.server != "localhost" else 5432))

def main():
    if not args.dropall and not args.create and not args.migration:
        parser.print_help()
        sys.exit(0)

    db = open_database_connection(getpass.getpass("DB Password > "))

    if args.dropall:
        print "Dropping all tables and types..."
        if raw_input("You are about to drop everything in production. Are you sure? ").lower()[0] != 'y':
            print "ERROR: Yeah right! Please confirm before dropping all tables!"
            return sys.exit(1)

        cursor = db.cursor()
        cursor.execute(LIST_TABLES_SQL)
        for table in cursor.fetchall():
            cursor.execute("DROP TABLE %s" % table[0])

        cursor.execute(LIST_TYPES_SQL)
        for ctype in cursor.fetchall():
            cursor.execute("DROP TYPE %s" % ctype[1])

        db.commit()

    if args.create:
        print "Creating all tables..."
        with open(os.path.join(DIR, "schema.sql"), "r") as f:
            cursor = db.cursor()
            cursor.execute(f.read())
            db.commit()

    if args.migration:
        migration = sorted(os.listdir(os.path.join(DIR, "migrations")))[-1]
        migration_path = os.path.join(DIR, "migrations", migration)
        print "Running migration %s..." % migration

        if not os.path.exists(os.path.join(migration_path, "migrate.py")):
            print "ERROR: No migrate.py for migration, cannot run!"

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

        print "MIGRATION FOR %s FINISHED!" % migration

main()

