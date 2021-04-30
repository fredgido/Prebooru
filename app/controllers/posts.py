# APP\CONTROLLERS\POSTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, url_for


# ## LOCAL IMPORTS

from ..models import IllustUrl, Post
from .base import GetSearch, ShowJson, IndexJson, IdFilter, Paginate, DefaultOrder, PageNavigation


# ## GLOBAL VARIABLES

bp = Blueprint("post", __name__)

# ## FUNCTIONS


@bp.route('/posts/<int:id>.json')
def show_json(id):
    return ShowJson(Post, id)


@bp.route('/posts/<int:id>')
def show_html(id):
    abort(404)


@bp.route('/posts.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/posts', methods=['GET'])
def index_html():
    q = index()
    posts = Paginate(q, request)
    return render_template("posts/index.html", posts=posts.items, page_html=PageNavigation(posts,request))


def index():
    search = GetSearch(request)
    print(search)
    q = Post.query
    q = IdFilter(q, search)
    q = DefaultOrder(q)
    if 'illust_id' in search:
        q = q.filter(Post.illust_urls.any(IllustUrl.illust.has(site_illust_id=search['illust_id'])))
    if 'illust_site_id' in search:
        q = q.filter(Post.illust_urls.any(IllustUrl.illust.has(site_id=search['illust_site_id'])))
    return q
