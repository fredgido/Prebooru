import urllib.parse
from flask import render_template, Markup

from ..sites import GetSiteDomain, GetSiteKey
from ..sources import DICT as SOURCEDICT, base as BASE_SOURCE
from .base_helper import SearchUrlFor

def SiteDataIterator(illust):
    site_data_json = illust.site_data.to_json()
    for key,val in site_data_json.items():
        if key not in ['id', 'type', 'illust_id']:
            yield key, val

def IllustHasImages(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.IllustHasImages(illust)

def IllustHasVideos(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.IllustHasImages(illust)

def OriginalUrl(illust_url):
    return 'https://' + GetSiteDomain(illust_url.site_id) + illust_url.url


def ShortLink(illust):
    site_key = GetSiteKey(illust.site_id)
    return "%s #%d" % (site_key.lower(), illust.site_illust_id)

def SiteIllustUrl(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.GetIllustUrl(illust.site_illust_id)


def PostSearch(illust):
    return SearchUrlFor('post.index_html', illust_urls={'illust_id': illust.id}) #, site_illust_id=illust.site_illust_id, isite_id=illust.site_id)


def PostPreviews(illust):
    posts = [post for post in illust.posts if post is not None]
    if len(posts) == 0:
        return  Markup('<i>No posts.</i>')
    #return render_template("illusts\_post_previews.html", posts=posts)
    return Markup(render_template("pools/_post_previews.html", posts=posts))

def DanbooruBatchUpload(illust):
    source = BASE_SOURCE._Source(illust.site_id)
    post_url = source.GetPostUrl(illust)
    query_string = urllib.parse.urlencode({'url': post_url})
    href_url = 'https://danbooru.donmai.us/uploads/batch?' + query_string
    return '<li id="subnav-batch-bookmarklet"><a id="subnav-batch-bookmarklet-link" href="%s">Batch bookmarklet</a></li>' % href_url
