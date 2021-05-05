from .base_helper import SearchUrlFor

def PostSearch(artist):
    return SearchUrlFor('post.index_html', site_artist_id=artist.site_artist_id, asite_id=artist.site_id)
