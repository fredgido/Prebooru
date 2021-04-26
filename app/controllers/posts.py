# APP\CONTROLLERS\POSTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request


# ## LOCAL IMPORTS

from ..models import IllustUrl, Post
from .base import GetSearch, ShowJson, IndexJson, IdFilter


# ## GLOBAL VARIABLES

bp = Blueprint("post", __name__)

# ## FUNCTIONS


@bp.route('/posts/<int:id>.json')
def show(id):
    return ShowJson(Post, id)


@bp.route('/posts.json', methods=['GET'])
def index():
    search = GetSearch(request)
    print(search)
    q = Post.query
    q = IdFilter(q, search)
    if 'illust_id' in search:
        q = q.filter(Post.illust_urls.any(IllustUrl.illust.has(site_illust_id=search['illust_id'])))
    if 'illust_site_id' in search:
        q = q.filter(Post.illust_urls.any(IllustUrl.illust.has(site_id=search['illust_site_id'])))
    return IndexJson(q, request)
