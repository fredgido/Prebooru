# APP/HELPERS/ILLUSTS_HELPERS.PY

# ##PYTHON IMPORTS
import urllib.parse
from flask import render_template, Markup

# ##LOCAL IMPORTS
from ..sites import GetSiteDomain, GetSiteKey
from ..sources import SOURCEDICT
from ..sources.base import GetSourceById
from .base_helper import SearchUrlFor


# ##GLOBAL VARIABLES

SITE_DATA_LABELS = {
    'site_updated': 'Updated',
    'site_uploaded': 'Uploaded',
}


# ##FUNCTIONS

# #### Form functions

def IsGeneralForm(form):
    return (form.artist_id.data is None) or (form.site_id.data is None)


def FormClass(form):
    CLASS_MAP = {
        None: "",
        1: "pixiv-data",
        3: "twitter-data",
    }
    return CLASS_MAP[form.site_id.data]


# #### Site content functions

def SiteMetricIterator(illust):
    site_data_json = illust.site_data.to_json()
    for key, val in site_data_json.items():
        if key in ['retweets', 'replies', 'quotes', 'bookmarks', 'views']:
            yield key, val


def SiteDateIterator(illust):
    site_data_json = illust.site_data.to_json()
    for key, val in site_data_json.items():
        if key in ['site_updated', 'site_uploaded']:
            yield SITE_DATA_LABELS[key], val


# #### Media functions

def IllustHasImages(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.IllustHasImages(illust)


def IllustHasVideos(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.IllustHasImages(illust)


def PostPreviews(illust):
    posts = [post for post in illust.posts if post is not None]
    if len(posts) == 0:
        return Markup('<i>No posts.</i>')
    return Markup(render_template("pools/_post_previews.html", posts=posts))


def IllustUrlsOrdered(illust):
    return sorted(illust.urls, key=lambda x: x.order)


# #### URL functions

def OriginalUrl(illust_url):
    return 'https://' + GetSiteDomain(illust_url.site_id) + illust_url.url


def ShortLink(illust):
    site_key = GetSiteKey(illust.site_id)
    return "%s #%d" % (site_key.lower(), illust.site_illust_id)


def SiteIllustUrl(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.GetIllustUrl(illust.site_illust_id)


def PostIllustUrl(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    post_url = source.GetPostUrl(illust)
    return '<a rel="external noreferrer nofollow" href="%s">&raquo;</a>' % post_url if post_url != source.GetIllustUrl(illust.site_illust_id) else ""


def PostIllustSearch(illust):
    return SearchUrlFor('post.index_html', illust_urls={'illust_id': illust.id})


def PostTagSearch(tag):
    return SearchUrlFor('post.index_html', illust_urls={'illust': {'tags': {'name': tag.name}}})


def DanbooruBatchUrl(illust):
    source = GetSourceById(illust.site_id)
    post_url = source.GetPostUrl(illust)
    query_string = urllib.parse.urlencode({'url': post_url})
    return 'https://danbooru.donmai.us/uploads/batch?' + query_string
