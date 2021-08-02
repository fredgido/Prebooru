# APP\SIMILARITY\__INIT__.PY

# LOCAL IMPORTS
from .. import DB

# COLLATION IMPORTS
from .similarity_data import SimilarityData  # noqa: F401
from .similarity_pool import SimilarityPool  # noqa: F401
from .similarity_pool_element import SimilarityPoolElement  # noqa: F401


# INITIALIZATION

SimilarityPoolElement.sibling = DB.relationship(SimilarityPoolElement, uselist=False, lazy=True)


# GLOBAL VARIABLES

NONCE = None
