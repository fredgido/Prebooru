# APP/MODELS/NOTATION.PY

# ##PYTHON IMPORTS
import datetime
from dataclasses import dataclass
from flask import url_for
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
    _pools = DB.relationship(PoolNotation, backref='item', lazy=True, cascade='all,delete')
    pools = association_proxy('_pools', 'pool')

    @property
    def show_url(self):
        return url_for("notation.show_html", id=self.id)

    def delete(self):
        pools = self.pools
        DB.session.delete(self)
        DB.session.commit()
        for pool in pools:
            pool._elements.reorder()
        if len(pools) > 0:
            DB.session.commit()

    @staticmethod
    def searchable_attributes():
        return ['id', 'body', 'created', 'updated']
