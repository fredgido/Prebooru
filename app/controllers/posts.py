# APP\CONTROLLERS\POSTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, url_for
from sqlalchemy.orm import lazyload


# ## LOCAL IMPORTS

from ..models import Artist, Illust, IllustUrl, Post
from .base import GetSearch, ShowJson, IndexJson, IdFilter, Paginate, DefaultOrder, PageNavigation


# ## GLOBAL VARIABLES

bp = Blueprint("post", __name__)

# ## FUNCTIONS


@bp.route('/posts/<int:id>.json')
def show_json(id):
    return ShowJson(Post, id)


@bp.route('/posts/<int:id>')
def show_html(id):
    post = Post.query.filter_by(id=id).first()
    return render_template("posts/show.html", post=post) if post is not None else abort(404)


@bp.route('/posts.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/', methods=['GET'])
@bp.route('/posts', methods=['GET'])
def index_html():
    q = index()
    posts = Paginate(q, request)
    return render_template("posts/index.html", posts=posts)


def index():
    search = GetSearch(request)
    print(search)
    q = Post.query
    q = q.options(lazyload('*'))
    q = IdFilter(q, search)
    q = DefaultOrder(q)
    if 'artist_id' in search:
        #q = q.filter(Post.illust_urls.any(IllustUrl.illust.has(Illust.artist.has(id=search['artist_id']))))
        q = q.unique_join(IllustUrl, Post.illust_urls).unique_join(Illust).filter(Illust.artist_id == search['artist_id'])
    if 'illust_id' in search:
        #q = q.filter(Post.illust_urls.any(IllustUrl.illust.has(id=search['illust_id'])))
        q = q.unique_join(IllustUrl, Post.illust_urls).filter(IllustUrl.illust_id == search['illust_id'])
    if 'site_illust_id' in search:
        #q = q.filter(Post.illust_urls.any(IllustUrl.illust.has(site_illust_id=search['site_illust_id'])))
        q = q.unique_join(IllustUrl, Post.illust_urls).unique_join(Illust).filter(Illust.site_illust_id == search['site_illust_id'])
    if 'isite_id' in search:
        #q = q.filter(Post.illust_urls.any(IllustUrl.illust.has(site_id=search['isite_id'])))
        q = q.unique_join(IllustUrl, Post.illust_urls).unique_join(Illust).filter(Illust.site_id == search['isite_id'])
    if 'site_artist_id' in search:
        print("site_artist_id", search['site_artist_id'])
        q = q.unique_join(IllustUrl, Post.illust_urls).unique_join(Illust).unique_join(Artist).filter(Artist.site_artist_id == search['site_artist_id'])
        #q = q.filter(Post.illust_urls.any(IllustUrl.illust.has(Illust.artist.has(site_artist_id=search['site_artist_id']))))
    if 'asite_id' in search:
        #q = q.filter(Post.illust_urls.any(IllustUrl.illust.has(Illust.artist.has(site_id=search['asite_id']))))
        q = q.unique_join(IllustUrl, Post.illust_urls).unique_join(Illust).unique_join(Artist).filter(Artist.site_id == search['asite_id'])
    return q