from .. import DB

class SimilarityPoolElement(DB.Model):
    __bind_key__ = 'similarity'
    id = DB.Column(DB.Integer, primary_key=True)
    pool_id = DB.Column(DB.Integer, DB.ForeignKey('similarity_pool.id'), nullable=False)
    post_id = DB.Column(DB.Integer, nullable=False)
    score = DB.Column(DB.Float, nullable=False)
