from ..sites import GetSiteKey
from ..sources import DICT as SOURCEDICT
from .base_helper import SearchUrlFor
from app.storage import CACHE_DATA_DIRECTORY, CACHE_NETWORK_URLPATH

def CacheUrl(md5):
    return CACHE_NETWORK_URLPATH + md5 + '.jpg'
