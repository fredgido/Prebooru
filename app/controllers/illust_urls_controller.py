# APP\CONTROLLERS\ILLUSTS.PY

# ## PYTHON IMPORTS
import json
from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash
from sqlalchemy.orm import selectinload, lazyload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS

from ..logical.utility import GetCurrentTime, EvalBoolString
from ..logical.logger import LogError
from ..models import Illust, Artist, Notation, Pool, IllustUrl
from ..sources import base as BASE_SOURCE
from ..database import local as DBLOCAL
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder, Paginate,\
    GetDataParams, CustomNameForm, ParseType, GetOrAbort, GetOrError, SetError, PutMethodCheck, UpdateColumnAttributes


# ## GLOBAL VARIABLES

bp = Blueprint("illust_url", __name__)

# Forms


def GetIllustUrlForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class IllustUrlForm(CustomNameForm):
        illust_id = IntegerField('Illust ID', id='illust-url-illust_id', custom_name='illust_url[illust_id]', validators=[DataRequired()])
        url = StringField('URL', id='illust-url-url', custom_name='illust_url[url]', validators=[DataRequired()])
        width = IntegerField('Width', id='illust-url-width', custom_name='illust_url[width]')
        height = IntegerField('Height', id='illust-url-height', custom_name='illust_url[height]')
        order = IntegerField('Order', id='illust-url-order', custom_name='illust_url[order]')
        active = BooleanField('Active', id='illust-url-active', custom_name='illust_url[active]', default=True)
    return IllustUrlForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions


def CheckCreateParams(dataparams):
    if dataparams['illust_id'] is None:
        return "No illust ID present!"
    if dataparams['url'] is None:
        return "No URL present!"


def ConvertCreateParams(dataparams):
    params = {}
    params['illust_id'] = ParseType(dataparams, 'illust_id', int)
    params['url'] = dataparams['url'] if len(dataparams['url'].strip()) > 0 else None
    params['width'] = ParseType(dataparams, 'width', int)
    params['height'] = ParseType(dataparams, 'height', int)
    params['order'] = ParseType(dataparams, 'order', int)
    params['active'] = ParseType(dataparams, 'active', EvalBoolString) or False
    return params


# #### Route helpers


def create(request):
    dataparams = GetDataParams(request, 'illust_url')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    error = CheckCreateParams(createparams)
    if error is not None:
        return SetError(retdata, error)
    illust = Illust.find(createparams['illust_id'])
    if illust is None:
        del createparams['illust_id']
        return SetError(retdata, "illust #%s not found." % dataparams['illust_id'])
    illust_url = BASE_SOURCE.CreateDBIllustUrlFromParams(createparams, illust)
    retdata['item'] = illust_url.to_json()
    return retdata


# #### Route functions


# ###### CREATE


@bp.route('/illust_urls/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = GetIllustUrlForm(**request.args)
    if form.illust_id.data is not None:
        illust = Illust.find(form.illust_id.data)
        if illust is None:
            flash("Illust #%d not a valid illust." % form.illust_id.data, 'error')
            form.illust_id.data = None
    return render_template("illust_urls/new.html", form=form)


@bp.route('/illust_urls', methods=['POST'])
def create_html():
    results = create(request)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('illust_url.new_html', **results['data']))
    return redirect(url_for('illust.show_html', id=results['data']['illust_id']))


 ###### CREATE


@bp.route('/illust_urls/<int:id>/edit', methods=['GET'])
def edit_html(id):
    """HTML access point to update function."""
    illust_url = GetOrAbort(IllustUrl, id)
    form = GetIllustUrlForm(**illust_url.__dict__)
    return render_template("illust_urls/edit.html", form=form, illust_url=illust_url)


@bp.route('/illust_urls/<int:id>', methods=['POST', 'PUT'])
def update_html(id):
    PutMethodCheck(request)
    illust_url = GetOrAbort(IllustUrl, id)
    dataparams = GetDataParams(request, 'illust_url')
    updateparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    is_dirty = UpdateColumnAttributes(illust_url, ['url', 'height', 'width', 'order', 'active'], dataparams, updateparams)
    if is_dirty:
        print("Changes detected.")
        DBLOCAL.SaveData()
    return redirect(url_for('illust.show_html', id=illust_url.illust_id))
