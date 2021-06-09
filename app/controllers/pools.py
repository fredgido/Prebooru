# APP\CONTROLLERS\POOLS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, url_for
from sqlalchemy.orm import lazyload, selectinload


# ## LOCAL IMPORTS

from ..models import Pool
from ..models import Illust
from ..models import IllustUrl
from .base import GetSearch, ShowJson, IndexJson, IdFilter, Paginate, DefaultOrder, PageNavigation, GetPage, GetLimit


# ## GLOBAL VARIABLES

bp = Blueprint("pool", __name__)

# ## FUNCTIONS


@bp.route('/pools/<int:id>.json')
def show_json(id):
    return ShowJson(Pool, id)


@bp.route('/pools/<int:id>')
def show_html(id):
    pool = Pool.query.filter_by(id=id).first()
    if pool is None:
        abort(404)
    illust_options = selectinload(Illust.urls).selectinload(IllustUrl.post).lazyload('*')
    elements = pool.element_paginate(page=GetPage(request), per_page=GetLimit(request), illust_options=illust_options)
    return render_template("pools/show.html", pool=pool, elements=elements)


@bp.route('/pools.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/pools', methods=['GET'])
def index_html():
    q = index()
    pools = Paginate(q, request)
    return render_template("pools/index.html", pools=pools)


def index():
    search = GetSearch(request)
    print(search)
    q = Pool.query
    q = IdFilter(q, search)
    q = DefaultOrder(q, search)
    return q
