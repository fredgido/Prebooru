from .. import DB

from .similarity_data import SimilarityData  # noqa: F401
from .similarity_pool import SimilarityPool  # noqa: F401
from .similarity_pool_element import SimilarityPoolElement

SimilarityPoolElement.sibling = DB.relationship(SimilarityPoolElement, uselist=False, lazy=True)

NONCE = None
