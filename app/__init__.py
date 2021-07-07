# APP\__INIT__.PY

# ## PYTHON IMPORTS
import os
from sqlalchemy import event, MetaData
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


# ## LOCAL IMPORTS
from .config import DB_PATH, CACHE_PATH, SIMILARITY_PATH


# ##GLOBAL VARIABLES

# For imports outside the relative path
PREBOORU_DB_URL = os.environ.get('PREBOORU_DB') if os.environ.get('PREBOORU_DB') is not None else 'sqlite:///%s' % DB_PATH
PREBOORU_CACHE_URL = os.environ.get('PREBOORU_CACHE') if os.environ.get('PREBOORU_CACHE') is not None else 'sqlite:///%s' % CACHE_PATH
PREBOORU_SIMILARITY_URL = os.environ.get('PREBOORU_SIMILARITY') if os.environ.get('PREBOORU_SIMILARITY') is not None else 'sqlite:///%s' % SIMILARITY_PATH

NAMING_CONVENTION = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


# ##FUNCTIONS


def _fk_pragma_on_connect(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL2")
    cursor.close()


# ##INITIALIZATION

PREBOORU_APP = Flask("prebooru", template_folder='app\\templates', static_folder='app\\static')
PREBOORU_APP.config.from_mapping(
    SQLALCHEMY_DATABASE_URI=PREBOORU_DB_URL,
    SQLALCHEMY_BINDS={
        'cache': PREBOORU_CACHE_URL,
        'similarity': PREBOORU_SIMILARITY_URL,
    },
    SQLALCHEMY_ECHO=False,
    SECRET_KEY='\xfb\x12\xdf\xa1@i\xd6>V\xc0\xbb\x8fp\x16#Z\x0b\x81\xeb\x16',
    DEBUG=True,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    EXPLAIN_TEMPLATE_LOADING=True
)

METADATA = MetaData(naming_convention=NAMING_CONVENTION)
DB = SQLAlchemy(PREBOORU_APP, metadata=METADATA)
SESSION = DB.session

event.listen(DB.engine, 'connect', _fk_pragma_on_connect)
event.listen(DB.get_engine(bind='cache'), 'connect', _fk_pragma_on_connect)
event.listen(DB.get_engine(bind='similarity'), 'connect', _fk_pragma_on_connect)


# Extend Python imports
from .logical import uniquejoin  # noqa: E402
uniquejoin.Initialize()
