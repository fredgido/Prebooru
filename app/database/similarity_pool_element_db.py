# APP/DATABASE/SIMILARITY_POOL_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from .. import SESSION
from ..similarity import SimilarityPoolElement


# ## FUNCTIONS

# #### Route DB functions

# ###### DELETE

def DeleteSimilarityPoolElement(similarity_pool_element):
    sibling_pool_element = similarity_pool_element.sibling
    similarity_pool_element.sibling_id = None
    if sibling_pool_element is not None:
        sibling_pool_element.sibling_id = None
    SESSION.commit()
    SESSION.delete(similarity_pool_element)
    if sibling_pool_element is not None:
        SESSION.delete(sibling_pool_element)
    SESSION.commit()


def BatchDeleteSimilarityPoolElement(similarity_pool_elements):
    pool_element_ids = [element.id for element in similarity_pool_elements]
    pool_element_ids += [element.sibling_id for element in similarity_pool_elements if element.sibling_id is not None]
    SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(pool_element_ids)).update({'sibling_id': None})
    SESSION.commit()
    SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(pool_element_ids)).delete()
    SESSION.commit()
