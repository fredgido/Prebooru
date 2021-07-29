# APP\CONTROLLERS\POSTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template
from sqlalchemy.orm import lazyload

# ## LOCAL IMPORTS
from ..models import Post
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate,\
    DefaultOrder, GetOrAbort


# ## GLOBAL VARIABLES

bp = Blueprint("post", __name__)


# ## FUNCTIONS

# #### Route auxiliary functions

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Post.query
    q = q.options(lazyload('*'))
    q = SearchFilter(q, search)
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
