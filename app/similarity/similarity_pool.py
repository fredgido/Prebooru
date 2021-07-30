# APP/SIMILARITY/SIMILARITY_POOL.PY

# ##PYTHON IMPORTS
import datetime
from types import SimpleNamespace
from dataclasses import dataclass
from sqlalchemy.orm import selectinload, lazyload

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel
from .similarity_pool_element import SimilarityPoolElement


# ##CLASSES

@dataclass
class SimilarityPool(JsonModel):
    __bind_key__ = 'similarity'

    id: int
    post_id: int
    total_results: int
    calculation_time: float
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = DB.Column(DB.Integer, primary_key=True)
    post_id = DB.Column(DB.Integer, nullable=False)
    total_results = DB.Column(DB.Integer, nullable=False)
    calculation_time = DB.Column(DB.Float, nullable=False)
    elements = DB.relationship(SimilarityPoolElement, lazy=True, backref=DB.backref('pool', lazy=True, uselist=False), cascade="all, delete")
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)

    def element_paginate(self, page=None, per_page=None, post_options=lazyload('*')):
        from ..models import Post
        q = SimilarityPoolElement.query
        q = q.options(selectinload(SimilarityPoolElement.sibling))
        q = q.filter_by(pool_id=self.id)
        q = q.order_by(SimilarityPoolElement.score.desc())
        page = q.paginate(per_page=per_page, page=page)
        post_ids = [element.post_id for element in page.items]
        post_options = post_options if type(post_options) is tuple else (post_options,)
        posts = Post.query.options(*post_options).filter(Post.id.in_(post_ids)).all() if len(post_ids) else []
        for i in range(len(page.items)):
            element = page.items[i]
            page.items[i] = SimpleNamespace(element=element, post=None)
            page.items[i].post = next(filter(lambda x: x.id == element.post_id, posts), None)
        return page

    def append(self, post_id, score):
        self._create_or_update_element(post_id, score)
        DB.session.commit()

    def update(self, results):
        for result in results:
            self._create_or_update_element(**result)
        DB.session.commit()

    def _create_or_update_element(self, post_id, score):
        element = next(filter(lambda x: x.post_id == post_id, self.elements), None)
        if element is None:
            element = SimilarityPoolElement(pool_id=self.id, post_id=post_id, score=score)
            DB.session.add(element)
        else:
            element.score = score
        return element
