# APP\CONTROLLERS\ILLUSTS.PY

# ## PYTHON IMPORTS
import json
from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash
from sqlalchemy.orm import selectinload, lazyload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired
from wtforms.widgets import HiddenInput

# ## LOCAL IMPORTS

from ..logical.utility import GetCurrentTime, EvalBoolString
from ..logical.logger import LogError
from ..models import Illust, Artist, Notation, Pool
from ..sources.base import GetSourceById, CreateDBIllustUrlFromParams
from ..database import local as DBLOCAL
from ..database.illust_db import CreateIllustFromParameters, UpdateIllustFromParameters
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder,\
    Paginate, GetDataParams, CustomNameForm, ParseType, GetOrAbort, GetOrError, SetError, HideInput, IntOrBlank,\
    NullifyBlanks, SetDefault, CheckParamRequirements, ParseStringList


# ## GLOBAL VARIABLES

bp = Blueprint("illust", __name__)


CREATE_REQUIRED_PARAMS = ['artist_id', 'site_id', 'site_illust_id']
UPDATE_REQUIRED_PARAMS = []


# Forms


def GetIllustForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class IllustForm(CustomNameForm):
        artist_id = IntegerField('Artist ID', id='illust-artist-id', custom_name='illust[artist_id]', validators=[DataRequired()])
        site_id = SelectField('Site', choices=[("", ""), ('1', 'Pixiv'), ('3', 'Twitter')], id='illust-site-id', custom_name='illust[site_id]', validators=[DataRequired()], coerce=IntOrBlank)
        site_illust_id = IntegerField('Site Illust ID', id='illust-site-illust-id', custom_name='illust[site_illust_id]', validators=[DataRequired()])
        site_created = StringField('Site Created', id='artist-site-created', custom_name='artist[site_created]', description='Format must be ISO8601 timestamp (e.g. 2021-05-24T04:46:51).')
        pages = IntegerField('Pages', id='illust-pages', custom_name='illust[pages]')
        score = IntegerField('Score', id='illust-score', custom_name='illust[score]')
        tag_string = TextAreaField('Tag string', id='illust-tag-string', custom_name='illust[tag_string]', description="Separated by whitespace.")
        commentary = TextAreaField('Commentary', id='illust-commentary', custom_name='illust[commentary]')
        active = BooleanField('Active', id='illust-active', custom_name='illust[active]')
    return IllustForm(**kwargs)


def GetIllustUrlForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class IllustUrlForm(CustomNameForm):
        url = StringField('URL', id='illust-url-url', custom_name='illust_url[url]', validators=[DataRequired()])
        width = IntegerField('Width', id='illust-width', custom_name='illust_url[width]')
        height = IntegerField('Height', id='illust-site-height', custom_name='illust_url[height]')
        order = IntegerField('Order', id='illust-site-order', custom_name='illust_url[order]')
        active = BooleanField('Active', id='illust-active', custom_name='illust_url[active]')
    return IllustUrlForm(**kwargs)


def GetAddPoolIllustForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class AddPoolIllustForm(CustomNameForm):
        pool_id = IntegerField('Pool ID', id='illust-pool-id', custom_name='illust[pool_id]', validators=[DataRequired()])
    return AddPoolIllustForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions

"""
def CheckDataParams(dataparams):
    if 'site_id' not in dataparams or not dataparams['site_id'].isdigit():
        return "No site ID present!"
    if 'site_illust_id' not in dataparams or not dataparams['site_illust_id'].isdigit():
        return "No site illust ID present!"
    if 'site_artist_id' not in dataparams or not dataparams['site_artist_id'].isdigit():
        return "No site artist ID present!"
"""

def ConvertDataParams(dataparams):
    params = GetIllustForm(**dataparams).data
    if 'tag_string' in dataparams:
        dataparams['tags'] = params['tags'] = ParseStringList(dataparams, 'tag_string', r'\s')
    params['active'] = EvalBoolString(dataparams['active']) if 'active' in dataparams else None
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    createparams = ConvertDataParams(dataparams)
    SetDefault(createparams, 'tags', [])
    createparams['commentaries'] = createparams['commentary']
    return createparams

"""
def ConvertDataParams(dataparams):
    dataparams['site_id'] = int(dataparams['site_id'])
    dataparams['site_illust_id'] = int(dataparams['site_illust_id'])
    dataparams['site_artist_id'] = int(dataparams['site_artist_id'])
    dataparams['pages'] = int(dataparams['pages'])
    if 'score' in dataparams:
        dataparams['score'] = int(dataparams['score'])
    if 'urls' in dataparams:
        dataparams['urls'] = [json.loads(url_json) for url_json in dataparams['urls']]
    if 'videos' in dataparams:
        dataparams['videos'] = [json.loads(url_json) for url_json in dataparams['videos']]


def CheckCreateParams(dataparams):
    if dataparams['site_id'] is None:
        return "No site ID present!"
    if dataparams['site_illust_id'] is None:
        return "No site illust ID present!"
    if dataparams['artist_id'] is None:
        return "No artist ID present!"


def ConvertCreateParams(dataparams):
    params = {}
    params['site_id'] = ParseType(dataparams, 'site_id', int)
    params['site_illust_id'] = ParseType(dataparams, 'site_illust_id', int)
    params['artist_id'] = ParseType(dataparams, 'artist_id', int)
    params['score'] = ParseType(dataparams, 'score', int)
    params['pages'] = ParseType(dataparams, 'pages', int)
    params['active'] = ParseType(dataparams, 'active', EvalBoolString) or False
    params['commentary'] = dataparams['commentary'] if len(dataparams['commentary'].strip()) > 0 else None
    params['tags'] = dataparams['tag_string'].split() if len(dataparams['tag_string']) > 0 else []
    return params
"""

def CheckCreateUrlParams(dataparams):
    if dataparams['url'] is None:
        return "No URL present!"


def ConvertCreateUrlParams(dataparams):
    params = {}
    params['url'] = dataparams['url'] if len(dataparams['url'].strip()) > 0 else None
    params['width'] = ParseType(dataparams, 'width', int)
    params['height'] = ParseType(dataparams, 'height', int)
    params['order'] = ParseType(dataparams, 'order', int)
    params['active'] = ParseType(dataparams, 'active', EvalBoolString) or False
    return params


# #### Route helpers


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Illust.query
    q = q.options(selectinload(Illust.site_data), lazyload('*'))
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


def create():
    dataparams = GetDataParams(request, 'illust')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    artist = Artist.find(createparams['artist_id'])
    if artist is None:
        createparams['artist_id'] = None
        return SetError(retdata, "artist #%s not found." % dataparams['artist_id'])
    illust = Illust.query.filter_by(site_id=createparams['site_id'], site_illust_id=createparams['site_illust_id']).first()
    if illust is not None:
        createparams['site_illust_id'] = None
        retdata['item'] = illust.to_json()
        return SetError(retdata, "Illust already exists: illust #%d" % illust.id)
    illust = CreateIllustFromParameters(createparams)
    retdata['item'] = illust.to_json()
    return retdata


# #### Route functions


# ###### SHOW/INDEX


@bp.route('/illusts/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Illust, id)


@bp.route('/illusts/<int:id>', methods=['GET'])
def show_html(id):
    illust = GetOrAbort(Illust, id)
    return render_template("illusts/show.html", illust=illust)


@bp.route('/illusts.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/illusts', methods=['GET'])
def index_html():
    q = index()
    illusts = Paginate(q, request)
    return render_template("illusts/index.html", illusts=illusts, illust=None)


# ###### CREATE


@bp.route('/illusts/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = GetIllustForm(**request.args)
    if form.artist_id.data is not None:
        artist = Artist.find(form.artist_id.data)
        if artist is None:
            flash("artist #%d not a valid artist." % form.artist_id.data, 'error')
            form.artist_id.data = None
        else:
            HideInput(form, 'artist_id', artist.id)
            HideInput(form, 'site_id', artist.site_id)
    return render_template("illusts/new.html", form=form, illust=None)


@bp.route('/illusts', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('illust.new_html', **results['data']))
    return redirect(url_for('illust.show_html', id=results['item']['id']))


@bp.route('/illusts.json', methods=['POST'])
def create_json():
    return create()


# ###### UPDATE


@bp.route('/illusts/<int:id>/edit', methods=['GET'])
def edit_html(id):
    """HTML access point to update function."""
    illust = GetOrAbort(Illust, id)
    form = GetIllustForm(site_id=illust.site_id, site_illust_id=illust.site_illust_id, artist_id=illust.artist_id, pages=illust.pages, score=illust.score, active=illust.active)
    return render_template("illusts/edit.html", form=form, illust=illust)


# ###### Illust URL


@bp.route('/illusts/<int:id>/illust_urls/new', methods=['GET'])
def new_illust_url_html(id):
    """HTML access point to create illust URL function."""
    artist_id = request.args.get('illust_id', type=int)
    illust = GetOrAbort(Illust, id)
    form = GetIllustUrlForm(active=True)
    return render_template("illusts/new_illust_url.html", form=form, illust=illust)


@bp.route('/illusts/<int:id>/illust_urls', methods=['POST'])
def create_illust_url_html(id):
    illust = GetOrAbort(Illust, id)
    dataparams = GetDataParams(request, 'illust_url')
    createparams = ConvertCreateUrlParams(dataparams)
    print(dataparams, createparams, request.values)
    error = CheckCreateUrlParams(createparams)
    if error is not None:
        return {'error': True, 'message': error, 'params': createparams}
    createparams['illust_id'] = illust.id
    CreateDBIllustUrlFromParams(createparams, illust)
    return redirect(url_for('illust.show_html', id=illust.id))


# ###### Pool

# ########## SHOW/INDEX


@bp.route('/illusts/<int:id>/pools.json', methods=['GET'])
def show_pools_json(id):
    illust = GetOrError(Illust, id)
    if type(illust) is dict:
        return illust
    pools = [pool.to_json() for pool in illust.pools]
    return jsonify(pools)


@bp.route('/illusts/pools.json', methods=['GET'])
def index_pools_json():
    illusts = index().all()
    retvalue = {}
    for illust in illusts:
        id_str = str(illust.id)
        pools = [pool.to_json() for pool in illust.pools]
        retvalue[id_str] = pools
    return retvalue


# ###### Notation


@bp.route('/illusts/<int:id>/notation.json', methods=['POST'])
def add_notation_json(id):
    illust = GetOrError(Illust, id)
    if type(illust) is dict:
        return illust
    dataparams = GetDataParams(request, 'illust')
    if 'notation' not in dataparams:
        return {'error': True, 'message': "Must include notation.", 'params': dataparams}
    current_time = GetCurrentTime()
    note = Notation(body=dataparams['notation'], created=current_time, updated=current_time)
    DBLOCAL.SaveData(note)
    illust.notations.append(note)
    DBLOCAL.SaveData()
    return {'error': False, 'note': note, 'illust': illust, 'params': dataparams}


# ###### Misc


@bp.route('/illusts/<int:id>/query_update', methods=['POST'])
def query_update_html(id):
    illust = GetOrAbort(Illust, id)
    source = GetSourceById(illust.site_id)
    updateparams = source.GetIllustData(illust.site_illust_id)
    if updateparams['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        updateparams['tags'] += [tag.name for tag in illust.tags if tag.name not in updateparams['tags']]
    updatelist = list(updateparams.keys())
    UpdateIllustFromParameters(illust, updateparams, updatelist)
    flash("Illust updated.")
    return redirect(url_for('illust.show_html', id=id))
