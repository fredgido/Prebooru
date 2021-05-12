import os
from .config import DB_PATH, CACHE_PATH
from sqlalchemy import event
from sqlalchemy.engine import Engine
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# For imports outside the relative path
PREBOORU_DB_URL = os.environ.get('PREBOORU_DB') if os.environ.get('PREBOORU_DB') is not None else 'sqlite:///%s' % DB_PATH
PREBOORU_CACHE_URL = os.environ.get('PREBOORU_CACHE') if os.environ.get('PREBOORU_CACHE') is not None else 'sqlite:///%s' % CACHE_PATH

app = Flask("prebooru", template_folder='app\\templates', static_folder='app\\static')  # See if I can rename this
app.config.from_mapping(
    SQLALCHEMY_DATABASE_URI= PREBOORU_DB_URL,
    SQLALCHEMY_BINDS = {
        'cache': PREBOORU_CACHE_URL,
    },
    SQLALCHEMY_ECHO=False,
    SECRET_KEY='\xfb\x12\xdf\xa1@i\xd6>V\xc0\xbb\x8fp\x16#Z\x0b\x81\xeb\x16',
    DEBUG=True,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    EXPLAIN_TEMPLATE_LOADING=True
)

db = SQLAlchemy(app)
session = db.session


def _fk_pragma_on_connect(dbapi_connection, connection_record):
    print("Executing PRAGMAs...")
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL2")
    cursor.close()

event.listen(db.engine, 'connect', _fk_pragma_on_connect)

import app.helpers as helpers
app.jinja_env.globals.update(helpers=helpers)

'''
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set sqlite's WAL mode."""
    print("Executing PRAGMAs...")
    #dbapi_connection.isolation_level = None
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
    #dbapi_connection.isolation_level = old_isolation
'''