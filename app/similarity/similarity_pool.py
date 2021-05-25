from .. import db
from .similarity_pool_element import SimilarityPoolElement


class SimilarityPool(db.Model):
    __bind_key__ = 'similarity'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    total_results = db.Column(db.Integer, nullable=False)
    calculation_time = db.Column(db.Float, nullable=False)
    elements = db.relationship(SimilarityPoolElement, lazy=False, backref=db.backref('pool', lazy=True), cascade="all, delete")
    created = db.Column(db.DateTime(timezone=False), nullable=False)
    updated = db.Column(db.DateTime(timezone=False), nullable=False)
    
    def append(self, post_id, score):
        self._create_or_update_element(post_id, score)
        db.session.commit()
    
    def update(self, results):
        for result in results:
            self._create_or_update_element(**result)
        db.session.commit()
    
    def _create_or_update_element(self, post_id, score):
        element = next(filter(lambda x: x.post_id == post_id, self.elements), None)
        if element is None:
            element = SimilarityPoolElement(pool_id=self.id, post_id=post_id, score=score)
            db.session.add(element)
        else:
            element.score = score
        return element