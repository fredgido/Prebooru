# APP\CONTROLLERS\POOL_ELEMENTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, url_for, flash, redirect
from wtforms import IntegerField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from ..models import Pool, PoolElement
from ..database.pool_element_db import CreatePoolElementFromParameters, DeletePoolElement
from .base_controller import GetDataParams, CustomNameForm, ReferrerCheck, GetOrAbort, GetOrError, CheckParamRequirements,\
    SetError, HideInput


# ## GLOBAL VARIABLES

bp = Blueprint("pool_element", __name__)

CREATE_REQUIRED_PARAMS = ['pool_id']

APPEND_KEYS = ['illust_id', 'post_id', 'notation_id']


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
    if (dataparams['illust_id'] is None) and (dataparams['post_id'] is None) and (dataparams['notation_id'] is None):
        return "No illust, post, or notation ID specified!"


def ConvertDataParams(dataparams):
    return GetPoolElementForm(**dataparams).data


# #### Route auxiliary functions

def create():
    dataparams = GetDataParams(request, 'pool_element')
    createparams = ConvertDataParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    check = CheckCreateParams(createparams)
    if check is not None:
        return SetError(retdata, check)
    pool = Pool.find(createparams['pool_id'])
    if pool is None:
        return SetError(retdata, "Pool #d not found." % createparams['pool_id'])
    retdata.update(CreatePoolElementFromParameters(pool, createparams))
    return retdata


def delete(pool_element):
    DeletePoolElement(pool_element)


# #### Route functions

# ###### CREATE

@bp.route('/pool_elements/new', methods=['GET'])
def new_html():
    """HTML access point to the create pool element function."""
    form = GetPoolElementForm(**request.args)
    if any((getattr(form, attr).data is not None) for attr in APPEND_KEYS):
        for key in APPEND_KEYS:
            HideInput(form, key)
    return render_template("pool_elements/new.html", form=form)


@bp.route('/pool_elements', methods=['POST'])
def create_html():
    result = create()
    if result['error']:
        flash(result['message'], 'error')
        if ReferrerCheck('pool_element.new_html', request):
            return redirect(url_for('pool_element.new_html', **result['dataparams']))
        else:
            return redirect(request.referrer)
    flash("Added to pool.")
    return redirect(url_for('%s.show_html' % result['type'], id=result['item']['id']))


@bp.route('/pool_elements.json', methods=['POST'])
def create_json():
    return create()


# ###### DELETE

@bp.route('/pool_elements/<int:id>', methods=['DELETE'])
def delete_html(id):
    pool_element = GetOrAbort(PoolElement, id)
    delete(pool_element)
    flash("Removed from pool.")
    return redirect(request.referrer)


@bp.route('/pool_elements/<int:id>.json', methods=['DELETE'])
def delete_json(id):
    pool_element = GetOrError(PoolElement, id)
    if type(pool_element) is dict:
        return pool_element
    return {'error': False}
