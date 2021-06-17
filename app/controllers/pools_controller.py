# APP\CONTROLLERS\POOLS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, url_for
from sqlalchemy.orm import lazyload, selectinload


# ## LOCAL IMPORTS
from .. import session as SESSION
from ..models import Pool
from ..models import Post
from ..models import Illust
from ..models import IllustUrl
from ..logical.utility import GetCurrentTime
from .base_controller import GetSearch, ShowJson, IndexJson, SearchFilter, IdFilter, Paginate, DefaultOrder, PageNavigation, GetPage, GetLimit, GetDataParams


# ## GLOBAL VARIABLES

bp = Blueprint("pool", __name__)

# ## FUNCTIONS

def ConvertDataParams(dataparams):
    if 'post_id' in dataparams:
        dataparams['post_id'] = int(dataparams['post_id'])
    if 'illust_id' in dataparams:
        dataparams['illust_id'] = int(dataparams['illust_id'])

@bp.route('/pools/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Pool, id)


@bp.route('/pools/<int:id>', methods=['GET'])
def show_html(id):
    pool = Pool.query.filter_by(id=id).first()
    if pool is None:
        abort(404)
    illust_options = (selectinload(Illust.urls).selectinload(IllustUrl.post).lazyload('*'), selectinload(Illust.notations))
    post_options = (selectinload(Post.notations), selectinload(Post.illust_urls).selectinload(IllustUrl.illust).lazyload('*'), lazyload('*'))
    elements = pool.element_paginate(page=GetPage(request), per_page=GetLimit(request), illust_options=illust_options, post_options=post_options)
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
    #q = IdFilter(q, search)
    q = SearchFilter(q, search, 'id', 'name', 'created', 'updated')
    q = DefaultOrder(q, search)
    return q

def AddTypeElement(pool, itemclass, id, dataparams):
    item = itemclass.find(id)
    if item is None:
        return {'error': True, 'message': "%s not found." % itemclass.__name__, 'parameters': dataparams}
    pool_ids = [pool.id for pool in item.pools]
    print("Pool IDs:", pool_ids)
    if pool.id in pool_ids:
        return {'error': True, 'message': "%s #%d already added to pool #%d." % (itemclass.__name__, item.id, pool.id), 'parameters': dataparams}
    pool.updated = GetCurrentTime()
    pool.elements.append(item)
    SESSION.commit()
    pool_ids += [pool.id]
    return {'error': False, 'pool': pool.to_json(), 'item': item.to_json(), 'data': pool_ids, 'params': dataparams}

@bp.route('/pools/<int:id>/element.json', methods=['POST'])
def add_element(id):
    print(request.values)
    pool = Pool.find(id)
    if pool is None:
        return {'error': True, 'message': "Pool not found."}
    dataparams = GetDataParams(request, 'pool')
    ConvertDataParams(dataparams)
    if 'post_id' in dataparams:
        return AddTypeElement(pool, Post, dataparams['post_id'], dataparams)
    elif 'illust_id' in dataparams:
        return AddTypeElement(pool, Illust, dataparams['illust_id'], dataparams)
    return {'error': True, 'message': "Must include illust or post ID.", 'parameters': dataparams}


