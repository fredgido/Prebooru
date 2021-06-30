from .base_helper import SearchUrlFor

def PostSearch(booru):
    return SearchUrlFor('post.index_html', illust_urls={'illust': {'artist': {'boorus': {'id': booru.id}}}})
