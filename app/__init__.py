import os
from .config import DB_PATH, CACHE_PATH, SIMILARITY_PATH
from sqlalchemy import event, MetaData
from sqlalchemy.engine import Engine
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# For imports outside the relative path
PREBOORU_DB_URL = os.environ.get('PREBOORU_DB') if os.environ.get('PREBOORU_DB') is not None else 'sqlite:///%s' % DB_PATH
PREBOORU_CACHE_URL = os.environ.get('PREBOORU_CACHE') if os.environ.get('PREBOORU_CACHE') is not None else 'sqlite:///%s' % CACHE_PATH
PREBOORU_SIMILARITY_URL = os.environ.get('PREBOORU_SIMILARITY') if os.environ.get('PREBOORU_SIMILARITY') is not None else 'sqlite:///%s' % SIMILARITY_PATH

app = Flask("prebooru", template_folder='app\\templates', static_folder='app\\static')  # See if I can rename this
app.config.from_mapping(
    SQLALCHEMY_DATABASE_URI= PREBOORU_DB_URL,
    SQLALCHEMY_BINDS = {
        'cache': PREBOORU_CACHE_URL,
        'similarity': PREBOORU_SIMILARITY_URL,
    },
    SQLALCHEMY_ECHO=False,
    SECRET_KEY='\xfb\x12\xdf\xa1@i\xd6>V\xc0\xbb\x8fp\x16#Z\x0b\x81\xeb\x16',
    DEBUG=True,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    EXPLAIN_TEMPLATE_LOADING=True
)

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
session = db.session

def _test_func(*args, **kwargs):
    print(args, kwargs)
    return True

def _fk_pragma_on_connect(dbapi_connection, connection_record):
    #print("Executing PRAGMAs...",dbapi_connection)
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL2")
    cursor.close()

event.listen(db.engine, 'connect', _fk_pragma_on_connect)
event.listen(db.get_engine(bind='cache'), 'connect', _fk_pragma_on_connect)
event.listen(db.get_engine(bind='similarity'), 'connect', _fk_pragma_on_connect)

"""
def _create_func_on_begin(dbapi_connection):
    print("Created func", dbapi_connection)
    dbapi_connection.connection.create_function('tegexp', 2, _test_func)
"""
#event.listen(db.get_engine(bind='similarity'), 'begin', _create_func_on_begin)


import app.helpers as helpers
app.jinja_env.globals.update(helpers=helpers)


import app.logical.uniquejoin as uniquejoin
uniquejoin.Initialize()

import re

import sqlalchemy as sa
import sqlalchemy.ext.declarative

engine = sa.create_engine('sqlite://', echo=True)

@sa.event.listens_for(engine, 'connect')
def sqlite_engine_connect(dbapi_conn, connection_record):
    dbapi_conn.create_function('regexp', 2, _regexp)

def _regexp(pattern, value):
    if value is None:
        return None
    return re.search(pattern, value) is not None

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