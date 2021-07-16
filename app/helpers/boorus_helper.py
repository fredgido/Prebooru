# APP/HELPERS/BOORUS_HELPER.PY

# ##PYTHON IMPORTS
import urllib.parse

# ##LOCAL IMPORTS
from ..config import DANBOORU_HOSTNAME
from .base_helper import SearchUrlFor


# ## FUNCTIONS


def IllustSearch(booru):
    return SearchUrlFor('illust.index_html', artist={'boorus': {'id': booru.id}})


def PostSearch(booru):
    return SearchUrlFor('post.index_html', illust_urls={'illust': {'artist': {'boorus': {'id': booru.id}}}})


def DanbooruPageLink(booru):
    return DANBOORU_HOSTNAME + '/artists/' + str(booru.danbooru_id)


def DanbooruPostSearch(booru):
    return DANBOORU_HOSTNAME + '/posts?' + urllib.parse.urlencode({'tags': booru.current_name})
