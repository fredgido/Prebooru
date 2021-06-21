import urllib.parse
from flask import render_template


from ..sources import base as BASE_SOURCE

def Preview(post):
    return render_template("posts/_preview.html", post=post)

def SimilarSearchLinks(post, format_url, proxy_url=None):
    image_links = []
    for i in range(0, len(post.illust_urls)):
        illust_url = post.illust_urls[i]
        illust = illust_url.illust
        if not illust.active:
            continue
        source = BASE_SOURCE._Source(illust_url.site_id)
        media_url = source.GetMediaUrl(illust_url)
        if source.IsVideoUrl(media_url):
            _, thumb_illust_url = source.VideoIllustDownloadUrls(illust)
            small_url = source.GetMediaUrl(thumb_illust_url)
        else:
            small_url = source.SmallImageUrl(media_url)
        #print("Small:", small_url)
        encoded_url = urllib.parse.quote_plus(small_url)
        href_url = format_url + encoded_url
        html = '<a href="%s">illust #%d</a>' % (href_url, illust.id )
        image_links.append(html)
    if proxy_url is not None:
        image_links.append('<a href="%s?post_id=%d">file</a>' % (proxy_url, post.id))
    return ' | '.join(image_links)

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
        source = BASE_SOURCE._Source(illust_url.site_id)
        media_url = source.GetMediaUrl(illust_url)
        post_url = source.GetPostUrl(illust)
        query_string = urllib.parse.urlencode({'url': media_url, 'ref': post_url})
        href_url = 'https://danbooru.donmai.us/uploads/new?' + query_string
        html = '<a href="%s">illust #%d</a>' % (href_url, illust.id)
        image_links.append(html)
    return ' | '.join(image_links)

def DanboooruBatchBookmarkletLinks(post):
    image_links = []
    for illust in post.illusts:
        if not illust.active:
            continue
        source = BASE_SOURCE._Source(illust.site_id)
        post_url = source.GetPostUrl(illust)
        query_string = urllib.parse.urlencode({'url': post_url})
        href_url = 'https://danbooru.donmai.us/uploads/batch?' + query_string
        html = '<a href="%s">illust #%d</a>' % (href_url, illust.id)
        image_links.append(html)
    return ' | '.join(image_links)
