from .. import db

class SimilarityPoolElement(db.Model):
    __bind_key__ = 'similarity'
    id = db.Column(db.Integer, primary_key=True)
    pool_id = db.Column(db.Integer, db.ForeignKey('similarity_pool.id'), nullable=False)
    post_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)
