# APP/MODELS/NOTATION.PY

# ##PYTHON IMPORTS
import datetime
from dataclasses import dataclass
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel
from .pool_element import PoolNotation

# ##GLOBAL VARIABLES


@dataclass
class Notation(JsonModel):
    id: int
    body: str
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.UnicodeText, nullable=False)
    created = db.Column(db.DateTime(timezone=False), nullable=False)
    updated = db.Column(db.DateTime(timezone=False), nullable=False)
    _pools = db.relationship(PoolNotation, backref='item', lazy=True, cascade='all,delete')
    pools = association_proxy('_pools', 'pool')

    def delete(self):
        pools = self.pools
        db.session.delete(self)
        db.session.commit()
        for pool in pools:
            pool._elements.reorder()
        if len(pools) > 0:
            db.session.commit()
