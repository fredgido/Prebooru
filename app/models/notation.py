# APP/MODELS/NOTATION.PY

# ##PYTHON IMPORTS
import datetime
from dataclasses import dataclass
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import DB
from .base import JsonModel
from .pool_element import PoolNotation


# ##GLOBAL VARIABLES

@dataclass
class Notation(JsonModel):
    id: int
    body: str
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = DB.Column(DB.Integer, primary_key=True)
    body = DB.Column(DB.UnicodeText, nullable=False)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)
    _pool = DB.relationship(PoolNotation, lazy=True, uselist=False, cascade='all,delete', backref=DB.backref('item', lazy=True, uselist=False))
    pool = association_proxy('_pool', 'pool')

    @property
    def append_type(self):
        if self._pool is not None:
            return 'pool'
        if self.artist is not None:
            return 'artist'
        if self.illust is not None:
            return 'illust'
        if self.post is not None:
            return 'post'

    def append_id(self, type):
        if type == 'pool':
            return self._pool.pool_id
        if type == 'artist':
            return self.artist.id
        if type == 'illust':
            return self.illust.id
        if type == 'post':
            return self.post.id

    @staticmethod
    def searchable_attributes():
        return ['id', 'body', 'created', 'updated']
