# APP/MODELS/POOL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import lazyload, selectin_polymorphic
from flask import url_for

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel
from .post import Post
from .illust import Illust
from .notation import Notation
from .pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation, pool_element_create, pool_element_delete


# ##GLOBAL VARIABLES

"""
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
"""

###ADD UPDATED/CREATED TO POOLS

@dataclass
class Pool(JsonModel):
    id: int
    name: str
    element_count: int
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    _elements = db.relationship(PoolElement, backref='pool', order_by=PoolElement.position, collection_class=ordering_list('position'), cascade='all,delete', lazy=True)
    elements = association_proxy('_elements', 'item', creator=lambda item: pool_element_create(item))
    created = db.Column(db.DateTime(timezone=False), nullable=True)
    updated = db.Column(db.DateTime(timezone=False), nullable=True)
    
    @property
    def element_count(self):
        return PoolElement.query.filter_by(pool_id=self.id).count()
    
    @property
    def show_url(self):
        return url_for("pool.show_html", id=self.id)
    
    def remove(self, item):
        pool_element_delete(self.id, item)
   
    def element_paginate(self, page=None, per_page=None, post_options=lazyload('*'), illust_options=lazyload('*'), notation_options=lazyload('*')):
        q = PoolElement.query
        q = q.options(selectin_polymorphic(PoolElement, [PoolIllust, PoolPost, PoolNotation]))
        q = q.filter_by(pool_id=self.id)
        q = q.order_by(PoolElement.position)
        page = q.paginate(per_page=per_page, page=page)
        post_ids = [element.post_id for element in page.items if element.type == 'pool_post']
        illust_ids = [element.illust_id for element in page.items if element.type == 'pool_illust']
        notation_ids = [element.notation_id for element in page.items if element.type == 'pool_notation']
        post_options = post_options if type(post_options) is tuple else (post_options,)
        posts = Post.query.options(*post_options).filter(Post.id.in_(post_ids)).all() if len(post_ids) else []
        illust_options = illust_options if type(illust_options) is tuple else (illust_options,)
        illusts = Illust.query.options(*illust_options).filter(Illust.id.in_(illust_ids)).all() if len(illust_ids) else []
        notation_options = notation_options if type(notation_options) is tuple else (notation_options,)
        notations = Notation.query.options(*notation_options).filter(Notation.id.in_(notation_ids)).all() if len(notation_ids) else []
        for i in range(0, len(page.items)):
            page_item = page.items[i]
            if page_item.type == 'pool_post':
                page.items[i] = next(filter(lambda x: x.id == page_item.post_id, posts))
            elif page_item.type == 'pool_illust':
                page.items[i] = next(filter(lambda x: x.id == page_item.illust_id, illusts))
            elif page_item.type == 'pool_notation':
                page.items[i] = next(filter(lambda x: x.id == page_item.notation_id, notations))
        return page
