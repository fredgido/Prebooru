from .. import DB

from .similarity_result import SimilarityResult
from .similarity_result2 import SimilarityResult2
from .similarity_result3 import SimilarityResult3
from .similarity_pool import SimilarityPool
from .similarity_pool_element import SimilarityPoolElement

SimilarityPoolElement.sibling = DB.relationship(SimilarityPoolElement, uselist=False, lazy=True)

NONCE = None
