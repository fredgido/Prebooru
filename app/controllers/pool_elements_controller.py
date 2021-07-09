# APP\CONTROLLERS\POOL_ELEMENTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, url_for, flash, redirect
from wtforms import IntegerField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from ..models import Pool, Post, Illust, Notation
from ..database import local as DBLOCAL
from ..logical.utility import GetCurrentTime
from .base_controller import GetDataParams, CustomNameForm, ParseType


# ## GLOBAL VARIABLES

bp = Blueprint("pool_element", __name__)

# Forms


def GetPoolElementForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class PoolElementForm(CustomNameForm):
        pool_id = IntegerField('Pool ID', id='pool-element-pool-id', custom_name='pool_element[pool_id]', validators=[DataRequired()])
        illust_id = IntegerField('Illust ID', id='pool-element-illust-id', custom_name='pool_element[illust_id]')
        post_id = IntegerField('Post ID', id='pool-element-post-id', custom_name='pool_element[post_id]')
        notation_id = IntegerField('Notation ID', id='pool-element-notation-id', custom_name='pool_element[notation_id]')
    return PoolElementForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions


def CheckCreateParams(dataparams):
    if dataparams['pool_id'] is None:
        return "No pool ID present!"
    if (dataparams['illust_id'] is None) and (dataparams['post_id'] is None) and (dataparams['notation_id'] is None):
        return "No illust, post, or notation ID specified!"


def ConvertCreateParams(dataparams):
    params = {}
    params['pool_id'] = ParseType(dataparams, 'pool_id', int)
    params['illust_id'] = ParseType(dataparams, 'illust_id', int)
    params['post_id'] = ParseType(dataparams, 'post_id', int)
    params['notation_id'] = ParseType(dataparams, 'notation_id', int)
    return params


def AddTypeElement(pool, itemclass, itemtype, id, dataparams):
    item = itemclass.find(id)
    if item is None:
        return {'error': True, 'message': "%s not found." % itemtype, 'dataparams': dataparams}
    pool_ids = [pool.id for pool in item.pools]
    print("Pool IDs:", pool_ids)
    if pool.id in pool_ids:
        return {'error': True, 'message': "%s #%d already added to pool #%d." % (itemtype, item.id, pool.id), 'dataparams': dataparams}
    pool.updated = GetCurrentTime()
    pool.elements.append(item)
    DBLOCAL.SaveData()
    pool_ids += [pool.id]
    return {'error': False, 'pool': pool.to_json(), 'type': itemtype, 'item': item.to_json(), 'data': pool_ids, 'dataparams': dataparams}


# #### Route Helpers


def create(request):
    dataparams = GetDataParams(request, 'pool_element')
    createparams = ConvertCreateParams(dataparams)
    check = CheckCreateParams(createparams)
    if check is not None:
        return {'error': True, 'message': check, 'dataparams': createparams}
    pool = Pool.find(createparams['pool_id'])
    if pool is None:
        return {'error': True, 'message': "Pool not found.", 'dataparams': createparams}
    if createparams['illust_id'] is not None:
        return AddTypeElement(pool, Illust, 'illust', createparams['illust_id'], createparams)
    if createparams['post_id'] is not None:
        return AddTypeElement(pool, Post, 'post', createparams['post_id'], createparams)
    if createparams['notation_id'] is not None:
        return AddTypeElement(pool, Notation, 'notation', createparams['notation_id'], createparams)


# #### Route functions

# ########## CREATE


@bp.route('/pool_elements/new', methods=['GET'])
def new_html():
    """HTML access point to the create pool element function."""
    '''
    pool_id = request.args.get('pool_id', type=int)
    illust_id = request.args.get('illust_id', type=int)
    post_id = request.args.get('post_id', type=int)
    notation_id = request.args.get('notation_id', type=int)
    '''
    form = GetPoolElementForm(**request.args)
    return render_template("pool_elements/new.html", form=form)


@bp.route('/pool_elements', methods=['POST'])
def create_html():
    result = create(request)
    if result['error']:
        flash(result['message'], 'error')
        return redirect(url_for('pool_element.new_html', **result['dataparams']))
    return redirect(url_for('%s.show_html' % result['type'], id=result['item']['id']))


@bp.route('/pool_elements.json', methods=['POST'])
def create_json():
    return create(request)
