# APP\HELPERS\SIMILARITY_HELPER.PY

# ## LOCAL IMPORTS
from ..storage import CACHE_NETWORK_URLPATH


# ## FUNCTIONS

def CacheUrl(md5):
    return CACHE_NETWORK_URLPATH + md5 + '.jpg'
