# APP\CONTROLLERS\BOORUS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from wtforms import TextAreaField, IntegerField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..models import Booru
from ..database.booru_db import CreateBooruFromParameters, CreateBooruFromID, UpdateBooruFromParameters, QueryUpdateBooru, CheckArtistsBooru
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, GetOrAbort, GetOrError,\
    PutMethodCheck, GetMethodRedirect, GetDataParams, SetError, SetDefault, CheckParamRequirements, NullifyBlanks, ParseStringList, CustomNameForm


# ## GLOBAL VARIABLES


bp = Blueprint("booru", __name__)


CREATE_REQUIRED_PARAMS = ['danbooru_id', 'current_name']
UPDATE_REQUIRED_PARAMS = []


# Forms


def GetBooruForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class BooruForm(CustomNameForm):
        danbooru_id = IntegerField('Danbooru ID', id='booru-danbooru-id', custom_name='booru[danbooru_id]', validators=[DataRequired()])
        current_name = StringField('Current Name', id='booru-current-name', custom_name='booru[current_name]', validators=[DataRequired()])
        name_string = TextAreaField('Names', id='booru-name-string', custom_name='booru[name_string]', description="Separated by whitespace.")
    return BooruForm(**kwargs)


# ## FUNCTIONS


# #### Helper functions


def ConvertDataParams(dataparams):
    params = GetBooruForm(**dataparams).data
    if 'name_string' in dataparams:
        dataparams['names'] = params['names'] = [name.lower() for name in ParseStringList(dataparams, 'name_string', r'\s')]
    params['current_name'] = params['current_name'].lower()
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    createparams = ConvertDataParams(dataparams)
    SetDefault(createparams, 'names', [])
    return createparams


def ConvertUpdateParams(dataparams):
    updateparams = ConvertDataParams(dataparams)
    for key in list(updateparams.keys()):
        if updateparams[key] is None:
            del updateparams[key]
    return updateparams


# #### Route auxiliary functions


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Booru.query
    q = q.options(selectinload(Booru.names), selectinload(Booru.artists).lazyload('*'))
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


def create():
    dataparams = GetDataParams(request, 'booru')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    print(dataparams, createparams)
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    booru = Booru.query.filter_by(danbooru_id=createparams['danbooru_id']).first()
    if booru is not None:
        createparams['danbooru_id'] = None
        return SetError(retdata, "Booru already exists: booru #%d" % booru.id)
    booru = CreateBooruFromParameters(createparams)
    retdata['item'] = booru.to_json()
    return retdata


def update(booru):
    dataparams = GetDataParams(request, 'booru')
    updateparams = ConvertUpdateParams(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    if 'danbooru_id' in updateparams and updateparams['danbooru_id'] != booru.danbooru_id:
        check_booru = Booru.query.filter_by(danbooru_id=updateparams['danbooru_id']).first()
        if check_booru is not None:
            return SetError(retdata, "Booru already exists: booru #%d" % check_booru.id)
    updatelist = list(set(dataparams.keys()).intersection(updateparams.keys()))
    UpdateBooruFromParameters(booru, updateparams, updatelist)
    retdata['item'] = booru.to_json()
    return retdata


# #### Route functions

# ###### SHOW/INDEX


@bp.route('/boorus/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Booru, id)


@bp.route('/boorus/<int:id>', methods=['GET'])
def show_html(id):
    booru = GetOrAbort(Booru, id)
    return render_template("boorus/show.html", booru=booru)


@bp.route('/boorus.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/boorus', methods=['GET'])
def index_html():
    q = index()
    boorus = Paginate(q, request)
    return render_template("boorus/index.html", boorus=boorus, booru=Booru())


# ###### CREATE


@bp.route('/boorus/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = GetBooruForm()
    return render_template("boorus/new.html", form=form, booru=Booru())


@bp.route('/boorus', methods=['POST'])
def create_html():
    if GetMethodRedirect(request):
        return index_html()
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('booru.new_html', **results['data']))
    return redirect(url_for('booru.show_html', id=results['item']['id']))


@bp.route('/boorus.json', methods=['POST'])
def create_json():
    if GetMethodRedirect(request):
        return index_json()
    return create()


# ###### UPDATE


@bp.route('/boorus/<int:id>/edit', methods=['GET'])
def edit_html(id):
    """HTML access point to update function."""
    booru = GetOrAbort(Booru, id)
    editparams = booru.to_json()
    editparams['name_string'] = '\r\n'.join(booru_name.name for booru_name in booru.names)
    form = GetBooruForm(**editparams)
    return render_template("boorus/edit.html", form=form, booru=booru)


@bp.route('/boorus/<int:id>', methods=['POST', 'PUT'])
def update_html(id):
    PutMethodCheck(request)
    booru = GetOrAbort(Booru, id)
    update(booru)
    return redirect(url_for('booru.show_html', id=booru.id))


@bp.route('/boorus/<int:id>', methods=['POST', 'PUT'])
def update_json(id):
    PutMethodCheck(request)
    booru = GetOrError(Booru, id)
    if type(booru) is dict:
        return booru
    return update(booru)


# ###### MISC


@bp.route('/boorus/query_create', methods=['POST'])
def query_create_html():
    params = {
        'danbooru_id': request.values.get('danbooru_id', type=int),
    }
    retdata = {'error': False, 'params': params}
    if params['danbooru_id'] is None:
        return SetError(retdata, "Must include the Danbooru ID.")
    booru = Booru.query.filter_by(danbooru_id=params['danbooru_id']).first()
    if booru is not None:
        retdata['item'] = booru.to_json()
        return SetError(retdata, "Booru already exists: booru #%d" % booru.id)
    results = CreateBooruFromID(params['danbooru_id'])
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    else:
        flash("Booru created.")
    return redirect(url_for('booru.show_html', id=results['item']['id']))


@bp.route('/boorus/<int:id>/query_update', methods=['POST'])
def query_update_html(id):
    booru = GetOrAbort(Booru, id)
    results = QueryUpdateBooru(booru)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Booru updated.")
    return redirect(url_for('booru.show_html', id=id))


@bp.route('/boorus/<int:id>/check_artists', methods=['POST'])
def check_artists_html(id):
    booru = GetOrAbort(Booru, id)
    results = CheckArtistsBooru(booru)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Booru updated.")
    return redirect(url_for('booru.show_html', id=id))
