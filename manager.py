# APP/STORAGE.PY

# ##PYTHON IMPORTS
import os
from flask.cli import with_appcontext
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand, stamp
from argparse import ArgumentParser, RawTextHelpFormatter

# ##LOCAL IMPORTS
from app.config import DB_PATH, CACHE_PATH, SIMILARITY_PATH


# ##FUNCTIONS


def init_db(make_new):
    check = input("This will destroy any existing information. Proceed (y/n)? ")
    if check.lower() != 'y':
        return
    if make_new:
        if os.path.exists(DB_PATH):
            print("Deleting prebooru database!")
            os.remove(DB_PATH)
        if os.path.exists(CACHE_PATH):
            print("Deleting cache database!")
            os.remove(CACHE_PATH)
        if os.path.exists(SIMILARITY_PATH):
            print("Deleting similarity database!")
            os.remove(SIMILARITY_PATH)

    from app import PREBOORU_APP, DB
    from app.models import NONCE  # noqa: F401
    from app.cache import NONCE  # noqa: F401
    from app.similarity import NONCE  # noqa: F401

    print("Creating tables")
    DB.drop_all()
    DB.create_all()

    print("Setting current migration to HEAD")
    migrate = Migrate(PREBOORU_APP, DB, render_as_batch=True)  # noqa: F841
    migrate.init_app(PREBOORU_APP)
    with PREBOORU_APP.app_context():
        stamp()


def migrate_db():
    from app import PREBOORU_APP, DB
    from app.models import NONCE  # noqa: F401
    from app.cache import NONCE  # noqa: F401
    from app.similarity import NONCE #noqa: F401

    migrate = Migrate(PREBOORU_APP, DB, render_as_batch=True)  # noqa: F841
    manager = Manager(PREBOORU_APP)
    manager.add_command('db', MigrateCommand)
    manager.run()


# For testing the programmatic use of alembic commands
def command_db():
    from flask_migrate import Migrate, current, stamp
    from app import PREBOORU_APP, DB

    migrate = Migrate(PREBOORU_APP, DB, render_as_batch=True)  # noqa: F841
    migrate.init_app(PREBOORU_APP)
    with PREBOORU_APP.app_context():
        current()


if __name__ == '__main__':
    parser = ArgumentParser(description="Stuff", formatter_class=RawTextHelpFormatter)
    parser.add_argument('operation', choices=['db', 'init', 'command'], help="DB: runs the migration manager\ninit: drops and recreates the tables")
    parser.add_argument('--new', required=False, action="store_true", default=False, help="Start with a new database file.")
    args, unknown = parser.parse_known_args()
    if args.operation == 'init':
        init_db(args.new)
    elif args.operation == 'db':
        migrate_db()
    elif args.operation == 'command':
        command_db()
