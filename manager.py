# APP/STORAGE.PY

# ##PYTHON IMPORTS
import os
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from argparse import ArgumentParser, RawTextHelpFormatter

# ##LOCAL IMPORTS
from app.config import DB_PATH


# ##FUNCTIONS


def init_db(make_new):
    check = input("This will destroy any existing information. Proceed (y/n)?")
    if check.lower() != 'y':
        return
    if make_new and os.path.exists(DB_PATH):
        print("Deleting database!")
        os.remove(DB_PATH)

    from app import db
    from app.models import NONCE  # noqa: F401
    from app.cache import NONCE  # noqa: F401

    class AlembicVersion(db.Model):
        version_num = db.Column(db.String(32), nullable=False, primary_key=True)

    print("Creating tables")
    db.drop_all()
    db.create_all()


def migrate_db():
    from app import app, db
    from app.models import NONCE  # noqa: F401
    from app.cache import NONCE  # noqa: F401

    migrate = Migrate(app, db, render_as_batch=True)  # noqa: F841
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    manager.run()


if __name__ == '__main__':
    parser = ArgumentParser(description="Stuff", formatter_class=RawTextHelpFormatter)
    parser.add_argument('operation', choices=['db', 'init'], help="db: runs the migration manager\ninit: drops and recreates the tables")
    parser.add_argument('--new', required=False, action="store_true", default=False, help="Start with a new database file.")
    args, unknown = parser.parse_known_args()
    if args.operation == 'init':
        init_db(args.new)
    else:
        migrate_db()
