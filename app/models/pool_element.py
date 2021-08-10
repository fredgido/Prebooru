# APP/MODELS/POOL_ELEMENT.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB, SESSION
from ..base_model import JsonModel, IntOrNone


# ##FUNCTIONS

def pool_element_create(item):
    if item.__table__.name == 'post':
        return PoolPost(item=item)
    if item.__table__.name == 'illust':
        return PoolIllust(item=item)
    if item.__table__.name == 'notation':
        return PoolNotation(item=item)
    raise Exception("Invalid pool type.")


def pool_element_delete(pool_id, item):
    table_name = item.__table__.name
    if table_name == 'post':
        element = PoolPost.query.filter_by(pool_id=pool_id, post_id=item.id).first()
    if table_name == 'illust':
        element = PoolIllust.query.filter_by(pool_id=pool_id, illust_id=item.id).first()
    if table_name == 'notation':
        element = PoolNotation.query.filter_by(pool_id=pool_id, notation_id=item.id).first()
    if element is None:
        raise Exception("%s #%d not found in pool #%d." % (table_name, item.id, pool_id))
    SESSION.delete(element)


# ##CLASSES

@dataclass
class PoolElement(JsonModel):
    __tablename__ = 'pool_element'

    id: int
    pool_id: int
    type: str

    id = DB.Column(DB.Integer, primary_key=True)
    pool_id = DB.Column(DB.Integer, DB.ForeignKey('pool.id'), nullable=False)
    position = DB.Column(DB.Integer, nullable=False)
    type = DB.Column(DB.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'pool_element',
        "polymorphic_on": type
    }


@dataclass
class PoolPost(PoolElement):
    __tablename__ = 'pool_post'

    post_id: IntOrNone
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'pool_post',
    }


@dataclass
class PoolIllust(PoolElement):
    __tablename__ = 'pool_illust'

    illust_id: IntOrNone
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'pool_illust',
    }


@dataclass
class PoolNotation(PoolElement):
    __tablename__ = 'pool_notation'

    notation_id: IntOrNone
    notation_id = DB.Column(DB.Integer, DB.ForeignKey('notation.id'), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'pool_notation',
    }
