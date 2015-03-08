#!/usr/bin/env python
import os, sys, getpass, argparse, psycopg2, redis, time

DIR = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument("-D", "--dropall", help="Drop all databases before creating", action="store_true")
parser.add_argument("-c", "--create", help="Create all unknown tables", action="store_true")
parser.add_argument("-m", "--migration", help="Run a migration", action="store_true")
parser.add_argument("-n", "--new", help="Create a new migration", action="store_true")
parser.add_argument("-u", "--username", help="PSQL Username", default="fort")
parser.add_argument("-s", "--server", help="PSQL Host", default="localhost")
parser.add_argument("-d", "--database", help="PSQL Database", default="fort")
parser.add_argument("-p", "--password", help="PSQL Password", default=None)
parser.add_argument("-g", "--generate", help="Generate fake data", action="store_true")

args = parser.parse_args()

args.username = args.username if args.username.startswith("fort_") else "fort"

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

MIGRATION_TEMPLATE = open("migrations/template.py", "r").read()

def open_database_connection(pw):
    return psycopg2.connect("host={host} port={port} dbname={db} user={user} password='{pw}'".format(
        host=args.server,
        user=args.username,
        db=args.database,
        pw=pw,
        port=50432 if args.server != "localhost" else 5432))

def main():
    if not args.dropall and not args.create and not args.migration and not args.new:
        parser.print_help()
        sys.exit(0)

    password = args.password or getpass.getpass("DB Password > ")
    db = open_database_connection(password)
    is_prod_db = args.database == "fort"

    if args.new:
        migrations = set(os.listdir("migrations")) - {"template.py"}
        id = str(int(max(migrations)) + 1).zfill(4)
        print "Creating migration #%s" % id

        os.mkdir("migrations/%s" % id)
        
        with open("migrations/%s/migrate.py" % id, "w") as f:
            f.write(MIGRATION_TEMPLATE.format(num=id, date=time.time()))
        
        print "  DONE"
        sys.exit(0)

    if args.dropall:
        print "Dropping all tables and types..."
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

        print "  Flushing redis..."
        redis.Redis().flushall()

        print "  DONE!"
        db.commit()

    if args.create:
        print "Creating all tables..."
        with open(os.path.join(DIR, "schema.sql"), "r") as f:
            cursor = db.cursor()
            cursor.execute(f.read())
            db.commit()

        print "  Conforming table ownership..."
        with db.cursor() as c:
            c.execute(LIST_TABLES_SQL)
            for table in c.fetchall():
                c.execute("ALTER TABLE %s OWNER TO %s" % (table[0], args.username))

            c.execute(LIST_TYPES_SQL)
            for ttype in c.fetchall():
                c.execute("ALTER TYPE %s OWNER TO %s" % (ttype[1], args.username))

        db.commit()
        print "  DONE!"

    if args.generate:
        print "Generating fake data..."
        from generate import DATA_GENERATORS

        with db.cursor() as c:
            for gen in DATA_GENERATORS:
                print "  running %s" % gen.__name__
                gen(c, db)
        db.commit()
        print "  DONE!"

    if args.migration:
        migration = max(set(os.listdir("migrations")) - {"template.py"})
        migration_path = os.path.join(DIR, "migrations", migration)
        print "Running migration %s..." % migration

        if not os.path.exists(os.path.join(migration_path, "migrate.py")):
            print "ERROR: No migrate.py for migration, cannot run!"

        code = {}
        exec open(os.path.join(migration_path, "migrate.py"), "r").read() in code

        db.autocommit = True
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

