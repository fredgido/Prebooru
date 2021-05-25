# APP/MODELS/POOL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel
from .post import Post


# ##GLOBAL VARIABLES

class PoolPosts(JsonModel):
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
    position = db.Column(db.Integer)
    post = db.relationship(Post, backref='_pools')

@dataclass
class Pool(JsonModel):
    id: int
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    _posts = db.relationship(PoolPosts, order_by=PoolPosts.position, backref='pool', collection_class=ordering_list('position'))
    posts = association_proxy('_posts', 'post', creator=lambda p: PoolPosts(post=p))
