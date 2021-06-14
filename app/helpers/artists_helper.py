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

def MainUrl(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ArtistMainUrl(artist)

def MediaUrl(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ArtistMediaUrl(artist)

def LikesUrl(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ArtistLikesUrl(artist)

def ArtistLinks(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    if not source.HasArtistUrls(artist):
        return '<em>N/A</em>'
    return ' | '.join([
        '<a href="%s">Main</a>' % MainUrl(artist),
        '<a href="%s">Media</a>' % MediaUrl(artist),
        '<a href="%s">Likes</a>' % LikesUrl(artist),
        ])
