# APP\CONTROLLERS\POOLS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, url_for, flash, redirect
from sqlalchemy.orm import lazyload, selectinload
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from ..models import Pool, Post, Illust, Notation, IllustUrl, PoolPost, PoolIllust, PoolNotation
from ..database import local as DBLOCAL
from ..logical.utility import GetCurrentTime
from ..logical.searchable import NumericMatching
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate,\
    DefaultOrder, GetDataParams, CustomNameForm, GetPage, GetLimit, ParseType


# ## GLOBAL VARIABLES

bp = Blueprint("pool", __name__)

# Forms


def GetPoolForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class PoolForm(CustomNameForm):
        name = StringField('Name', id='pool-name', custom_name='pool[name]', validators=[DataRequired()])
    return PoolForm(**kwargs)


def GetPoolElementForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class PoolElementForm(CustomNameForm):
        pool_id = IntegerField('Pool ID', id='pool-element-pool-id', custom_name='pool_element[pool_id]')
        illust_id = IntegerField('Illust ID', id='pool-element-illust-id', custom_name='pool_element[illust_id]')
        post_id = IntegerField('Post ID', id='pool-element-post-id', custom_name='pool_element[post_id]')
        notation_id = IntegerField('Notation ID', id='pool-element-notation-id', custom_name='pool_element[notation_id]')
    return PoolElementForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions


def ConvertDataParams(dataparams):
    if 'post_id' in dataparams:
        dataparams['post_id'] = int(dataparams['post_id'])
    if 'illust_id' in dataparams:
        dataparams['illust_id'] = int(dataparams['illust_id'])


def PoolNameUniqueness(name):
    check_pool = Pool.query.filter_by(name=name).first()
    if check_pool is not None:
        flash("Pool #%d already has name: %s" % (check_pool.id, check_pool.name))
        return False
    return True


def CheckPoolElementParams(dataparams):
    if dataparams['pool_id'] is None:
        return "No pool ID present!"
    if (dataparams['illust_id'] is None) and (dataparams['post_id'] is None) and (dataparams['notation_id'] is None):
        return "No illust, post, or notation ID specified!"


def ConvertPoolElementParams(dataparams):
    params = {}
    params['pool_id'] = ParseType(dataparams, 'pool_id', int)
    params['illust_id'] = ParseType(dataparams, 'illust_id', int)
    params['post_id'] = ParseType(dataparams, 'post_id', int)
    params['notation_id'] = ParseType(dataparams, 'notation_id', int)
    return params


def CreatePoolElementAbort(message, params):
    flash(message, 'error')
    return redirect(url_for('pool.new_pool_element_html', **params))


def AddTypeElement(pool, itemclass, itemtype, id, dataparams):
    item = itemclass.find(id)
    if item is None:
        return {'error': True, 'message': "%s not found." % itemtype, 'parameters': dataparams}
    pool_ids = [pool.id for pool in item.pools]
    print("Pool IDs:", pool_ids)
    if pool.id in pool_ids:
        return {'error': True, 'message': "%s #%d already added to pool #%d." % (itemtype, item.id, pool.id), 'parameters': dataparams}
    pool.updated = GetCurrentTime()
    pool.elements.append(item)
    DBLOCAL.SaveData()
    pool_ids += [pool.id]
    return {'error': False, 'pool': pool.to_json(), 'type': itemtype, 'item': item.to_json(), 'data': pool_ids, 'params': dataparams}


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    print("Params:", params, flush=True)
    print("Search:", search, flush=True)
    q = Pool.query
    q = SearchFilter(q, search)
    if 'post_id' in search:
        q = q.unique_join(PoolPost, Pool._elements)
        q = q.filter(NumericMatching(PoolPost, 'post_id', search['post_id']))
    elif 'illust_id' in search:
        q = q.unique_join(PoolIllust, Pool._elements)
        q = q.filter(NumericMatching(PoolIllust, 'illust_id', search['illust_id']))
    elif 'notation_id' in search:
        q = q.unique_join(PoolNotation, Pool._elements)
        q = q.filter(NumericMatching(PoolNotation, 'notation_id', search['notation_id']))
    q = DefaultOrder(q, search)
    return q


# #### Route functions

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
    return render_template("pools/index.html", pools=pools, pool=None)


@bp.route('/pools/new', methods=['GET'])
def new_html():
    form = GetPoolForm()
    return render_template("pools/new.html", form=form, pool=None)


@bp.route('/pools', methods=['POST'])
def create_html():
    print("create_html")
    dataparams = GetDataParams(request, 'pool')
    if 'name' not in dataparams:
        abort(405, "Must include name.")
    print(dataparams)
    if not PoolNameUniqueness(dataparams['name']):
        return redirect(url_for('pool.new_html'))
    current_time = GetCurrentTime()
    pool = Pool(name=dataparams['name'], created=current_time, updated=current_time)
    DBLOCAL.SaveData(pool)
    return redirect(url_for('pool.show_html', id=pool.id))


@bp.route('/pools/<int:id>/edit', methods=['GET'])
def edit_html(id):
    pool = Pool.find(id)
    if pool is None:
        abort(404)
    form = GetPoolForm(name=pool.name)
    return render_template("pools/edit.html", form=form, pool=pool)


@bp.route('/pools/<int:id>', methods=['POST', 'PUT'])
def update_html(id):
    print("update_html", request.method, request.values.get('_method'))
    if request.method == 'POST' and request.values.get('_method', default='').upper() != 'PUT':
        abort(405)
    pool = Pool.find(id)
    if pool is None:
        abort(404)
    is_dirty = False
    dataparams = GetDataParams(request, 'pool')
    print(dataparams)
    if 'name' in dataparams and pool.name != dataparams['name']:
        if not PoolNameUniqueness(dataparams['name']):
            return redirect(url_for('pool.edit_html', id=pool.id))
        print("Updating pool.")
        pool.name = dataparams['name']
        is_dirty = True
    if is_dirty:
        print("Changes detected.")
        pool.updated = GetCurrentTime()
        DBLOCAL.SaveData()
    return redirect(url_for('pool.show_html', id=pool.id))
