# APP/MODELS/ARTISTS_HELPER.PY

# ## PYTHON IMPORTS
from flask import Markup

# ## LOCAL IMPORTS
from ..sites import GetSiteKey
from ..sources import SOURCEDICT
from .base_helper import SearchUrlFor


# ## FUNCTIONS


def ShortLink(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ARTIST_SHORTLINK % artist.site_artist_id


def HrefUrl(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ARTIST_HREFURL % artist.site_artist_id


def PostSearch(artist):
    return SearchUrlFor('post.index_html', illust_urls={'illust': {'artist_id': artist.id}})


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
    all_links = ['<a href="%s">%s</a>' % (url, name.title()) for (name, url) in source.ArtistLinks(artist).items()]
    return Markup(' | '.join(all_links))


def WebpageLink(url):
    return '<a href="%s">%s</a>' % (url, url)
