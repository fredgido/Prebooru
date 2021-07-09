# APP\CONTROLLERS\ARTISTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, redirect, url_for, flash
from sqlalchemy.orm import selectinload, lazyload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..logical.utility import GetCurrentTime, EvalBoolString
from ..logical.logger import LogError
from ..models import Artist, Label
from ..sources import base as BASE_SOURCE
from ..database import local as DBLOCAL, base as DBBASE, artist_db as ARTISTDB
from ..database.artist_db import CreateArtistFromParameters, UpdateArtistFromParameters
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate,\
    DefaultOrder, GetDataParams, CustomNameForm, ParseType, UpdateColumnAttributes, UpdateRelationshipCollections,\
    GetOrAbort, GetOrError, SetError, ParseStringList, CheckParamRequirements, IntOrBlank, NullifyBlanks, SetDefault

# ## GLOBAL VARIABLES

bp = Blueprint("artist", __name__)

CREATE_REQUIRED_PARAMS = ['site_id', 'site_artist_id']
UPDATE_REQUIRED_PARAMS = []

# Forms


def GetArtistForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class ArtistForm(CustomNameForm):
        site_id = SelectField('Site', choices=[("", ""), (1, 'Pixiv'), (3, 'Twitter')], id='artist-site-id', custom_name='artist[site_id]', validators=[DataRequired()], coerce=IntOrBlank)
        site_artist_id = IntegerField('Site Artist ID', id='artist-site-artist-id', custom_name='artist[site_artist_id]', validators=[DataRequired()])
        current_site_account = StringField('Current Site Account', id='artist-current-site-account', custom_name='artist[current_site_account]')
        site_created = StringField('Site Created', id='artist-site-created', custom_name='artist[site_created]', description='Format must be ISO8601 timestamp (e.g. 2021-05-24T04:46:51).')
        account_string = TextAreaField('Site Accounts', id='artist-account-string', custom_name='artist[account_string]', description="Separated by whitespace.")
        name_string = TextAreaField('Site Names', id='artist-name-string', custom_name='artist[name_string]', description="Separated by carriage returns.")
        webpage_string = TextAreaField('Webpages', id='artist-webpage-string', custom_name='artist[webpage_string]', description="Separated by carriage returns. Prepend with '-' to mark as inactive.")
        profile = TextAreaField('Profile', id='artist-profile', custom_name='artist[profile]')
        active = BooleanField('Active', id='artist-active', custom_name='artist[active]', default=True)
    return ArtistForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions


def ConvertDataParams(dataparams):
    params = GetArtistForm(**dataparams).data
    print("-1", params, dataparams, request.values)
    if 'account_string' in dataparams:
        dataparams['site_accounts'] = params['site_accounts'] = ParseStringList(dataparams, 'account_string', r'\s')
    if 'name_string' in dataparams:
        dataparams['names'] = params['names'] = ParseStringList(dataparams, 'name_string', r'\r?\n')
    if 'webpage_string' in dataparams:
        dataparams['webpages'] = params['webpages'] = ParseStringList(dataparams, 'webpage_string', r'\r?\n')
    params['active'] = EvalBoolString(dataparams['active']) if 'active' in dataparams else None
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    createparams = ConvertDataParams(dataparams)
    SetDefault(createparams, 'site_accounts', [])
    SetDefault(createparams, 'names', [])
    SetDefault(createparams, 'webpages', [])
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
    q = Artist.query
    q = q.options(selectinload(Artist.names), selectinload(Artist.site_accounts), selectinload(Artist.webpages), lazyload(Artist.profiles))
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


def create():
    dataparams = GetDataParams(request, 'artist')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    artist = Artist.query.filter_by(site_id=createparams['site_id'], site_artist_id=dataparams['site_artist_id']).first()
    if artist is not None:
        createparams['site_artist_id'] = None
        return SetError(retdata, "Artist already exists: artist #%d" % artist.id)
    artist = CreateArtistFromParameters(createparams)
    retdata['item'] = artist.to_json()
    return retdata

    #artist = BASE_SOURCE.CreateDBArtistFromParams(dataparams)
    #artist_json = artist.to_json() if artist is not None else artist
    #return {'error': False, 'artist': artist_json}


def update(id):
    if request.method == 'POST' and request.values.get('_method', default='').upper() != 'PUT':
        abort(405)
    artist = GetOrAbort(Artist, id)
    dataparams = GetDataParams(request, 'artist')
    updateparams = ConvertUpdateParams(dataparams)
    updatelist = list(set(dataparams.keys()).intersection(updateparams.keys()))
    print("#0", dataparams.keys(), updateparams.keys())
    UpdateArtistFromParameters(artist, updateparams, updatelist)
    return artist


# #### Route functions

# ###### SHOW/INDEX


@bp.route('/artists/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Artist, id)


@bp.route('/artists/<int:id>', methods=['GET'])
def show_html(id):
    artist = GetOrAbort(Artist, id)
    return render_template("artists/show.html", artist=artist)


@bp.route('/artists.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/artists', methods=['GET'])
def index_html():
    q = index()
    artists = Paginate(q, request)
    return render_template("artists/index.html", artists=artists, artist=None)


# ###### CREATE


@bp.route('/artists/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = GetArtistForm()
    return render_template("artists/new.html", form=form, artist=None)


@bp.route('/artists', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('artist.new_html', **results['data']))
    return redirect(url_for('artist.show_html', id=results['item']['id']))


@bp.route('/artists.json', methods=['post'])
def create_json():
    dataparams = GetDataParams(request, 'artist')
    error = CheckDataParams(dataparams)
    if error is not None:
        return {'error': True, 'message': error, 'params': dataparams}
    ConvertDataParams(dataparams)
    artist = Artist.query.filter_by(site_id=dataparams['site_id'], site_artist_id=dataparams['site_artist_id']).first()
    if artist is not None:
        return {'error': True, 'message': "Artist already exists.", 'params': dataparams, 'artist': artist}
    try:
        artist = BASE_SOURCE.CreateDBArtistFromParams(dataparams)
    except Exception as e:
        print("Database exception!", e)
        LogError('controllers.artists.create', "Unhandled exception occurred creating artist: %s" % (str(e)))
        request.environ.get('werkzeug.server.shutdown')()
        return {'error': True, 'message': 'Database exception! Check log file.'}
    artist_json = artist.to_json() if artist is not None else artist
    return {'error': False, 'artist': artist_json}


# ###### UPDATE


@bp.route('/artists/<int:id>/edit', methods=['GET'])
def edit_html(id):
    """HTML access point to update function."""
    artist = GetOrAbort(Artist, id)
    editparams = artist.to_json()
    editparams['account_string'] = '\r\n'.join(site_account.name for site_account in artist.site_accounts)
    editparams['name_string'] = '\r\n'.join(artist_name.name for artist_name in artist.names)
    editparams['webpage_string'] = '\r\n'.join(( ('' if webpage.active else '-') + webpage.url) for webpage in artist.webpages)
    form = GetArtistForm(**editparams)
    return render_template("artists/edit.html", form=form, artist=artist)


@bp.route('/artists/<int:id>', methods=['POST', 'PUT'])
def update_html(id):
    artist = update(id)
    return redirect(url_for('artist.show_html', id=artist.id))

"""
@bp.route('/artists/<int:id>', methods=['POST', 'PUT'])
def update_html(id):
    print("update_html", request.method, request.values.get('_method'))
    if request.method == 'POST' and request.values.get('_method', default='').upper() != 'PUT':
        abort(405)
    artist = GetOrAbort(Artist, id)
    is_dirty = False
    dataparams = GetDataParams(request, 'artist')
    updateparams = ConvertUpdateParams(dataparams)
    print(dataparams, updateparams)
    UpdateArtistFromParameters(artist, updateparams, updatelist)
    is_dirty = UpdateColumnAttributes(artist, ['site_id', 'site_artist_id', 'current_site_account', 'active'], dataparams, updateparams)
    is_dirty = UpdateRelationshipCollections(artist, [('site_accounts', 'name', Label), ('names', 'name', Label)], dataparams, updateparams) or is_dirty
    if is_dirty:
        print("Changes detected.")
        artist.updated = GetCurrentTime()
        DBLOCAL.SaveData()
    return redirect(url_for('artist.show_html', id=artist.id))
"""

# ###### MISC


@bp.route('/artists/query_create.json', methods=['post'])
def query_create_json():
    """Query source and create artist."""
    site_id = request.values.get('site_id', type=int)
    site_artist_id = request.values.get('site_artist_id', type=int)
    if site_id is None or site_artist_id is None:
        return {'error': True, 'message': "Must include the site ID and site artist ID."}
    artist = Artist.query.filter_by(site_id=site_id, site_artist_id=site_artist_id).first()
    if artist is not None:
        return {'error': True, 'message': "Artist already exists.", 'params': {'site_id': site_id, 'site_artist_id': site_artist_id}, 'artist': artist}
    try:
        artist = BASE_SOURCE.QueryCreateArtist(site_id, site_artist_id)
    except Exception as e:
        print("Database exception!", e)
        LogError('controllers.artists.create', "Unhandled exception occurred query/creating artist: %s" % (str(e)))
        request.environ.get('werkzeug.server.shutdown')()
        return {'error': True, 'message': 'Database exception! Check log file.'}
    artist_json = artist.to_json() if artist is not None else artist
    return {'error': False, 'artist': artist_json}


@bp.route('/artists/<int:id>/query_update', methods=['GET'])
def query_update_html(id):
    """Query source and update artist."""
    artist = GetOrAbort(Artist, id)
    BASE_SOURCE.UpdateArtist(artist)
    flash("Artist updated.")
    return redirect(url_for('artist.show_html', id=id))


@bp.route('/artists/<int:id>/query_booru', methods=['GET'])
def query_booru_html(id):
    """Query booru and create/update booru relationships."""
    artist = GetOrAbort(Artist, id)
    response = BASE_SOURCE.QueryArtistBoorus(artist)
    if response['error']:
        flash(response['message'])
    else:
        flash('Artist updated.')
    return redirect(url_for('artist.show_html', id=id))


@bp.route('/artists/<int:id>/query_booru.json', methods=['GET'])
def query_booru_json(id):
    artist = GetOrError(Artist, id)
    if type(artist) is dict:
        return artist
    response = BASE_SOURCE.QueryArtistBoorus(artist)
    if response['error']:
        return response
    response['artist'] = response['artist'].to_json()
    response['boorus'] = [booru.to_json() for booru in response['boorus']]
    return response
