from ..sites import GetSiteKey
from ..sources import DICT as SOURCEDICT
from .base_helper import SearchUrlFor

def ShortLink(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ARTIST_SHORTLINK % artist.site_artist_id

def HrefUrl(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ARTIST_HREFURL % artist.site_artist_id

def PostSearch(artist):
    return SearchUrlFor('post.index_html', artist_id=artist.id)
