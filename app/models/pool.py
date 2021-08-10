# APP/MODELS/POOL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import lazyload, selectin_polymorphic
from flask import url_for

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel, DateTimeOrNull
from .post import Post
from .illust import Illust
from .notation import Notation
from .pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation, pool_element_create, pool_element_delete


# ##CLASSES

@dataclass
class Pool(JsonModel):
    id: int
    name: str
    element_count: int
    created: DateTimeOrNull
    updated: DateTimeOrNull
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(255), nullable=False)
    _elements = DB.relationship(PoolElement, backref='pool', order_by=PoolElement.position, collection_class=ordering_list('position'), cascade='all,delete', lazy=True)
    elements = association_proxy('_elements', 'item', creator=lambda item: pool_element_create(item))
    created = DB.Column(DB.DateTime(timezone=False), nullable=True)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=True)

    @property
    def element_count(self):
        return PoolElement.query.filter_by(pool_id=self.id).count()

    @property
    def show_url(self):
        return url_for("pool.show_html", id=self.id)

    def remove(self, item):
        pool_element_delete(self.id, item)

    def insert_before(self, insert_item, mark_item):
        pool_element = self._get_mark_element(mark_item)
        element_position = pool_element.position
        self.elements.insert(element_position, insert_item)

    def _get_mark_element(self, mark_item):
        pool_element = next(filter(lambda x: x.pool_id == self.id, mark_item._pools), None)
        if pool_element is None:
            raise Exception("Could not find mark item %s #%d in pool #%d")
        return pool_element

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

    @staticmethod
    def searchable_attributes():
        return ['id', 'name', 'created', 'updated']
