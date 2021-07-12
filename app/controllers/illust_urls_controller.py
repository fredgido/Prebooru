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
from ..sources.base import GetImageSiteId, GetImageSource
from ..database import local as DBLOCAL
from ..database.illust_url_db import CreateIllustUrlFromParameters
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder, Paginate,\
    GetDataParams, CustomNameForm, ParseType, GetOrAbort, GetOrError, SetError, PutMethodCheck, UpdateColumnAttributes,\
    NullifyBlanks, CheckParamRequirements, HideInput


# ## GLOBAL VARIABLES

bp = Blueprint("illust_url", __name__)

CREATE_REQUIRED_PARAMS = ['illust_id', 'url']
UPDATE_REQUIRED_PARAMS = []


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


def ConvertDataParams(dataparams):
    params = GetIllustUrlForm(**dataparams).data
    params['active'] = EvalBoolString(dataparams['active']) if 'active' in dataparams else None
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    return ConvertDataParams(dataparams)


# #### Route helpers


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = IllustUrl.query
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


def create(request):
    dataparams = GetDataParams(request, 'illust_url')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    illust = Illust.find(createparams['illust_id'])
    if illust is None:
        createparams['illust_id'] = None
        return SetError(retdata, "Illust #%d not found." % dataparams['illust_id'])
    source = GetImageSource(createparams['url'])
    if source is None:
        createparams['url'] = None
        return SetError(retdata, "URL is not a valid image URL from a recognized source." % dataparams['illust_id'])
    partial_url = source.PartialMediaUrl(createparams['url'])
    site_id = GetImageSiteId(createparams['url'])
    illust_url = IllustUrl.query.filter_by(site_id=site_id, url=partial_url).first()
    if illust_url is not None:
        createparams['url'] = None
        return SetError(retdata, "URL already on illust #%d." % illust_url.illust_id)
    createparams.update({'site_id': site_id, 'url': partial_url})
    illust_url = CreateIllustUrlFromParameters(createparams)
    retdata['item'] = illust_url.to_json()
    return retdata


# #### Route functions


# ###### SHOW/INDEX


@bp.route('/illust_urls/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(IllustUrl, id)


@bp.route('/illust_urls/<int:id>', methods=['GET'])
def show_html(id):
    illust_url = GetOrAbort(IllustUrl, id)
    return render_template("illust_urls/show.html", illust_url=illust_url)


@bp.route('/illust_urls.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/illust_urls', methods=['GET'])
def index_html():
    q = index()
    illust_urls = Paginate(q, request)
    return render_template("illust_urls/index.html", illust_urls=illust_urls, illust_url=None)


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
        else:
            HideInput(form, 'illust_id', illust.id)
    return render_template("illust_urls/new.html", form=form, illust_url=None)


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
    HideInput(form, 'illust_id', illust_url.illust_id)
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
