# APP\CONTROLLERS\POSTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, url_for, jsonify
from sqlalchemy.orm import selectinload, lazyload


# ## LOCAL IMPORTS

from ..logical.file import PutGetRaw
from ..logical.utility import GetCurrentTime, GetBufferChecksum
from ..database import local as DBLOCAL
from ..models import Artist, Illust, IllustUrl, Notation, Post
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, GetDataParams


# ## GLOBAL VARIABLES

bp = Blueprint("post", __name__)

# ## FUNCTIONS


@bp.route('/posts/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Post, id)


@bp.route('/posts/<int:id>', methods=['GET'])
def show_html(id):
    post = Post.find(id)
    return render_template("posts/show.html", post=post) if post is not None else abort(404)

@bp.route('/posts/<int:id>/pools.json', methods=['GET'])
def show_pools_json(id):
    post = Post.find(id)
    pools = [pool.to_json() for pool in post.pools]
    return jsonify(pools)


@bp.route('/posts.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)

@bp.route('/posts/pools.json', methods=['GET'])
def index_pools_json():
    posts = index().all()
    retvalue = {}
    for post in posts:
        id_str = str(post.id)
        pools = [pool.to_json() for pool in post.pools]
        retvalue[id_str] = pools
    return retvalue

@bp.route('/', methods=['GET'])
@bp.route('/posts', methods=['GET'])
def index_html():
    q = index()
    posts = Paginate(q, request)
    return render_template("posts/index.html", posts=posts)


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    print("Params:", params, flush=True)
    print("Search:", search, flush=True)
    q = Post.query
    q = q.options(lazyload('*'))
    q = SearchFilter(q, search)
    """
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
    """
    q = DefaultOrder(q, search)
    return q

@bp.route('/posts/<int:id>/update', methods=['GET'])
def update_html(id):
    post = Post.find(id)
    if post is None:
        abort(404)
    #BASE_SOURCE.UpdateIllust(illust)
    return redirect(url_for('post.show_html', id=id))

@bp.route('/posts/<int:id>/check.json', methods=['GET'])
def check_json(id):
    post = Post.find(id)
    if post is None:
        abort(404)
    buffer = PutGetRaw(post.file_path, 'rb')
    current_md5 = GetBufferChecksum(buffer)
    data_md5 = post.md5
    return {'current_md5': current_md5, 'data_md5': data_md5}

@bp.route('/posts/<int:id>/notation.json', methods=['POST'])
def add_notation(id):
    post = Post.find(id)
    if post is None:
        return {'error': True, 'message': "Post #%d not found." % id}
    dataparams = GetDataParams(request, 'post')
    if 'notation' not in dataparams or len(dataparams['notation'].strip()) == 0:
        return {'error': True, 'message': "Must include notation.", 'params': dataparams}
    current_time = GetCurrentTime()
    note = Notation(body=dataparams['notation'], created=current_time, updated=current_time)
    DBLOCAL.SaveData(note)
    post.notations.append(note)
    DBLOCAL.SaveData()
    return {'error': False, 'note': note, 'post': post, 'params': dataparams}
