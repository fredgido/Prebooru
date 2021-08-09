# APP\CONTROLLERS\POSTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template
from sqlalchemy import not_, or_
from sqlalchemy.orm import lazyload

# ## LOCAL IMPORTS
from ..models import Post, Illust, IllustUrl, PoolPost, PoolIllust
from ..logical.utility import EvalBoolString, IsFalsey
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate,\
    DefaultOrder, GetOrAbort


# ## GLOBAL VARIABLES

bp = Blueprint("post", __name__)

POST_POOLS_SUBQUERY = Post.query.join(PoolPost, Post._pools).filter(Post.id == PoolPost.post_id).with_entities(Post.id)
ILLUST_POOLS_SUBQUERY = Post.query.join(IllustUrl, Post.illust_urls).join(Illust, IllustUrl.illust).join(PoolIllust, Illust._pools).filter(Illust.id == PoolIllust.illust_id).with_entities(Post.id)

POOL_SEARCH_KEYS = ['has_pools', 'has_post_pools', 'has_illust_pools']


# ## FUNCTIONS

# #### Query functions

def PoolFilter(query, search):
    pool_search_key = next((key for key in POOL_SEARCH_KEYS if key in search), None)
    if pool_search_key is not None and EvalBoolString(search[pool_search_key]) is not None:
        if pool_search_key == 'has_pools':
            subclause = or_(Post.id.in_(POST_POOLS_SUBQUERY), Post.id.in_(ILLUST_POOLS_SUBQUERY))
        elif pool_search_key == 'has_post_pools':
            subclause = Post.id.in_(POST_POOLS_SUBQUERY)
        elif pool_search_key == 'has_illust_pools':
            subclause = Post.id.in_(ILLUST_POOLS_SUBQUERY)
        if IsFalsey(search[pool_search_key]):
            subclause = not_(subclause)
        query = query.filter(subclause)
    elif 'pool_id' in search and search['pool_id'].isdigit():
        query = query.unique_join(PoolPost, Post._pools).filter(PoolPost.pool_id == int(search['pool_id']))
    return query


# #### Route auxiliary functions

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    negative_search = GetParamsValue(params, 'not', True)
    q = Post.query
    q = q.options(lazyload('*'))
    q = SearchFilter(q, search, negative_search)
    q = PoolFilter(q, search)
    q = DefaultOrder(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/posts/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Post, id)


@bp.route('/posts/<int:id>', methods=['GET'])
def show_html(id):
    post = GetOrAbort(Post, id)
    return render_template("posts/show.html", post=post)


# ###### INDEX

@bp.route('/posts.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/', methods=['GET'])
@bp.route('/posts', methods=['GET'])
def index_html():
    q = index()
    posts = Paginate(q, request)
    return render_template("posts/index.html", posts=posts, post=Post())
