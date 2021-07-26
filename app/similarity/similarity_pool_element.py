from dataclasses import dataclass

from .. import DB
from ..base_model import JsonModel

@dataclass
class SimilarityPoolElement(JsonModel):
    __bind_key__ = 'similarity'
    id: int
    pool_id: int
    post_id: int
    score: float
    id = DB.Column(DB.Integer, primary_key=True)
    pool_id = DB.Column(DB.Integer, DB.ForeignKey('similarity_pool.id'), nullable=False)
    sibling_id = DB.Column(DB.Integer, DB.ForeignKey('similarity_pool_element.id'), nullable=True)
    post_id = DB.Column(DB.Integer, nullable=False)
    score = DB.Column(DB.Float, nullable=False)
