from .. import DB
from .similarity_pool_element import SimilarityPoolElement


class SimilarityPool(DB.Model):
    __bind_key__ = 'similarity'
    id = DB.Column(DB.Integer, primary_key=True)
    post_id = DB.Column(DB.Integer, nullable=False)
    total_results = DB.Column(DB.Integer, nullable=False)
    calculation_time = DB.Column(DB.Float, nullable=False)
    elements = DB.relationship(SimilarityPoolElement, lazy=True, backref=DB.backref('pool', lazy=True), cascade="all, delete")
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)
    
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