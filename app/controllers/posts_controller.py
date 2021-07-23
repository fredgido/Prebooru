# APP\CONTROLLERS\POSTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, url_for, jsonify, redirect
from sqlalchemy.orm import selectinload, lazyload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS

from ..logical.file import PutGetRaw
from ..logical.utility import GetCurrentTime, GetBufferChecksum
from ..database import local as DBLOCAL
from ..models import Artist, Illust, IllustUrl, Notation, Post, Pool
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, GetDataParams, ParseType, CustomNameForm, GetOrAbort, GetOrError


# ## GLOBAL VARIABLES

bp = Blueprint("post", __name__)

def GetAddPoolForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class AddPoolForm(CustomNameForm):
        pool_id = IntegerField('Pool ID', id='post-pool-id', custom_name='post[pool_id]', validators=[DataRequired()])
    return AddPoolForm(**kwargs)

# ## FUNCTIONS

def HTMLPostExistenceCheck(id):
    post = Post.find(id)
    if post is None:
        abort(404, "Post not found.")
    return post

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
    return render_template("posts/index.html", posts=posts, post=Post())


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Post.query
    q = q.options(lazyload('*'))
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q

@bp.route('/posts/<int:id>/update', methods=['GET'])
def update_html(id):
    post = GetOrAbort(Post, id)
    return redirect(url_for('post.show_html', id=id))

@bp.route('/posts/<int:id>/check.json', methods=['GET'])
def check_json(id):
    post = GetOrAbort(Post, id)
    buffer = PutGetRaw(post.file_path, 'rb')
    current_md5 = GetBufferChecksum(buffer)
    data_md5 = post.md5
    return {'current_md5': current_md5, 'data_md5': data_md5}

@bp.route('/posts/<int:id>/notation.json', methods=['POST'])
def add_notation_json(id):
    post = GetOrError(Post, id)
    if type(post) is dict:
        return post
    dataparams = GetDataParams(request, 'post')
    if 'notation' not in dataparams or len(dataparams['notation'].strip()) == 0:
        return {'error': True, 'message': "Must include notation.", 'params': dataparams}
    current_time = GetCurrentTime()
    note = Notation(body=dataparams['notation'], created=current_time, updated=current_time)
    DBLOCAL.SaveData(note)
    post.notations.append(note)
    DBLOCAL.SaveData()
    return {'error': False, 'note': note, 'post': post, 'params': dataparams}

@bp.route('/posts/<int:id>/pools/new', methods=['GET'])
def add_new_pool_html(id):
    post = HTMLPostExistenceCheck(id)
    form = GetAddPoolForm()
    return render_template("posts/add_pool.html", form=form, post=post)

@bp.route('/posts/<int:id>/pools', methods=['POST'])
def add_pool_html(id):
    post = HTMLPostExistenceCheck(id)
    dataparams = GetDataParams(request, 'post')
    pool_id = ParseType(dataparams, 'pool_id', int)
    if pool_id is None:
        flash("Must include valid pool ID.", 'error')
        redirect(url_for('post.add_new_pool_html', id=id))
    pool = Pool.find(pool_id)
    if pool is None:
        flash("Pool #%d not found." % pool_id, 'error')
        redirect(url_for('post.add_new_pool_html', id=id))
    pool_ids = [pool.id for pool in post.pools]
    if pool.id in pool_ids:
        flash("Post #%d already in pool #%d." % (post.id, pool.id), 'error')
        redirect(url_for('post.add_new_pool_html', id=id))
    pool.updated = GetCurrentTime()
    pool.elements.append(post)
    DBLOCAL.SaveData()
    return redirect(url_for('post.show_html', id=id))
