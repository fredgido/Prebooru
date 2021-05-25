# APP/MODELS/POOL_ELEMENT.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class PoolElement(JsonModel):
    id: int
    id = db.Column(db.Integer, primary_key=True)
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
