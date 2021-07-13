import urllib.parse

from ..config import DANBOORU_HOSTNAME
from .base_helper import SearchUrlFor

def PostSearch(booru):
    return SearchUrlFor('post.index_html', illust_urls={'illust': {'artist': {'boorus': {'id': booru.id}}}})

def DanbooruPageLink(booru):
    return DANBOORU_HOSTNAME + '/artists/' + str(booru.danbooru_id)

def DanbooruPostSearch(booru):
    return DANBOORU_HOSTNAME + '/posts?' + urllib.parse.urlencode({'tags': booru.current_name})
