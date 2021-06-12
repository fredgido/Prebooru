import urllib.parse
from flask import render_template


from ..sources import base as BASE_SOURCE

def Preview(post):
    return render_template("posts/_preview.html", post=post)

def SimilarSearchLinks(post, format_url):
    image_links = []
    for i in range(0, len(post.illust_urls)):
        illust_url = post.illust_urls[i]
        source = BASE_SOURCE._Source(illust_url.site_id)
        media_url = source.GetMediaUrl(illust_url)
        small_url = source.SmallImageUrl(media_url)
        #print("Small:", small_url)
        encoded_url = urllib.parse.quote_plus(small_url)
        href_url = format_url + encoded_url
        html = '<a href="%s">image #%d</a>' % (href_url, i + 1)
        image_links.append(html)
    return ' | '.join(image_links)

def DanbooruSearchLinks(post):
    return SimilarSearchLinks(post, 'https://danbooru.donmai.us/iqdb_queries?url=')

def SauceNAOSearchLinks(post):
    return SimilarSearchLinks(post, 'https://saucenao.com/search.php?db=999&url=')

def Ascii2DSearchLinks(post):
    return SimilarSearchLinks(post, 'https://ascii2d.net/search/url/')

def IQDBOrgSearchLinks(post):
    return SimilarSearchLinks(post, 'https://iqdb.org/?url=')

def DanbooruUploadLinks(post, format_url):
    image_links = []
    for i in range(0, len(post.illust_urls)):
        illust_url = post.illust_urls[i]
        source = BASE_SOURCE._Source(illust_url.site_id)
        media_url = source.GetMediaUrl(illust_url)
        post_url = source.GetPostUrl(illust_url.illust)
        query_string = urllib.parse.urlencode({'url': media_url, 'ref': post_url})
        href_url = format_url + query_string
        html = '<a href="%s">image #%d</a>' % (href_url, i + 1)
        image_links.append(html)
    return ' | '.join(image_links)

def DanbooruPostBookmarkletLinks(post):
    return DanbooruUploadLinks(post, 'https://danbooru.donmai.us/uploads/new?')

def DanboooruBatchBookmarkletLinks(post):
    return DanbooruUploadLinks(post, 'https://danbooru.donmai.us/uploads/batch?')
