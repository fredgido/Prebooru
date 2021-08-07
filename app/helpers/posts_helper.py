# APP/HELPERS/POSTS_HELPER.PY

# ##PYTHON IMPORTS
from flask import Markup
import urllib.parse

# ##LOCAL IMPORTS
from ..sources.base import GetSourceById
from .base_helper import SearchUrlFor, ExternalLink


# ## GLOBAL VARIABLES

DANBOORU_UPLOAD_LINK = 'https://danbooru.donmai.us/uploads/new?prebooru_post_id='


# ## FUNCTIONS

def SimilarSearchLinks(post, format_url, proxy_url=None):
    image_links = []
    for i in range(0, len(post.illust_urls)):
        illust_url = post.illust_urls[i]
        illust = illust_url.illust
        if not illust.active:
            continue
        source = GetSourceById(illust_url.site_id)
        media_url = source.GetMediaUrl(illust_url)
        if source.IsVideoUrl(media_url):
            _, thumb_illust_url = source.VideoIllustDownloadUrls(illust)
            small_url = source.GetMediaUrl(thumb_illust_url)
        else:
            small_url = source.SmallImageUrl(media_url)
        encoded_url = urllib.parse.quote_plus(small_url)
        href_url = format_url + encoded_url
        html = '<a href="%s">illust #%d</a>' % (href_url, illust.id)
        image_links.append(ExternalLink(illust.shortlink, href_url))
    if len(image_links) == 0 and proxy_url is not None:
        image_links.append(ExternalLink('file', proxy_url + '?post_id=' + str(post.id)))
    return Markup(' | ').join(image_links)


def DanbooruSearchLinks(post):
    return SimilarSearchLinks(post, 'https://danbooru.donmai.us/iqdb_queries?url=', '/proxy/danbooru_iqdb')


def SauceNAOSearchLinks(post):
    return SimilarSearchLinks(post, 'https://saucenao.com/search.php?db=999&url=', '/proxy/saucenao')


def Ascii2DSearchLinks(post):
    return SimilarSearchLinks(post, 'https://ascii2d.net/search/url/', '/proxy/ascii2d')


def IQDBOrgSearchLinks(post):
    return SimilarSearchLinks(post, 'https://iqdb.org/?url=')


def DanbooruPostBookmarkletLinks(post):
    image_links = []
    for i in range(0, len(post.illust_urls)):
        illust_url = post.illust_urls[i]
        illust = illust_url.illust
        if not illust.active:
            continue
        source = GetSourceById(illust_url.site_id)
        media_url = source.GetMediaUrl(illust_url)
        post_url = source.GetPostUrl(illust)
        query_string = urllib.parse.urlencode({'url': media_url, 'ref': post_url})
        href_url = 'https://danbooru.donmai.us/uploads/new?' + query_string
        html = '<a href="%s" target="_blank">illust #%d</a>' % (href_url, illust.id)
        image_links.append(ExternalLink(illust.shortlink, href_url))
    if len(image_links) == 0:
        image_links.append(ExternalLink('file', DANBOORU_UPLOAD_LINK + str(post.id)))
    return Markup(' | ').join(image_links)


def RelatedPostsSearch(post):
    illust_ids_str = ','.join([str(illust.id) for illust in post.illusts])
    return SearchUrlFor('post.index_html', illust_urls={'illust_id': illust_ids_str})
