# APP/MODELS/POOL_ELEMENT.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel, IntOrNone


# ##GLOBAL VARIABLES

def pool_element_create(item):
    if item.__table__.name == 'post':
        return PoolPost(item=item)
    if item.__table__.name == 'illust':
        return PoolIllust(item=item)
    if item.__table__.name == 'notation':
        return PoolNotation(item=item)
    raise Exception("Invalid pool type.")

@dataclass
class PoolElement(JsonModel):
    __tablename__ = 'pool_element'
    id: int
    pool_id: int
    type: str
    id = db.Column(db.Integer, primary_key=True)
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'pool_element',
        "polymorphic_on": type
    }

@dataclass
class PoolPost(PoolElement):
    __tablename__ = 'pool_post'
    post_id: IntOrNone
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'pool_post',
    }

@dataclass
class PoolIllust(PoolElement):
    __tablename__ = 'pool_illust'
    illust_id: IntOrNone
    illust_id = db.Column(db.Integer, db.ForeignKey('illust.id'), nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'pool_illust',
    }

@dataclass
class PoolNotation(PoolElement):
    __tablename__ = 'pool_notation'
    notation_id: IntOrNone
    notation_id = db.Column(db.Integer, db.ForeignKey('notation.id'), nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'pool_notation',
    }
