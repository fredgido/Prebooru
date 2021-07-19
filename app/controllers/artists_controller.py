# APP\CONTROLLERS\ARTISTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.orm import selectinload, lazyload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..logical.utility import EvalBoolString
from ..models import Artist
from ..sources import base as BASE_SOURCE
from ..database.local import IsError
from ..database.artist_db import CreateArtistFromParameters, UpdateArtistFromParameters
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate,\
    DefaultOrder, GetDataParams, CustomNameForm, GetOrAbort, GetOrError, SetError, ParseStringList, CheckParamRequirements,\
    IntOrBlank, NullifyBlanks, SetDefault, PutMethodCheck, GetMethodRedirect

# ## GLOBAL VARIABLES

bp = Blueprint("artist", __name__)

CREATE_REQUIRED_PARAMS = ['site_id', 'site_artist_id']


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


def update(artist):
    dataparams = GetDataParams(request, 'artist')
    updateparams = ConvertUpdateParams(dataparams)
    updatelist = list(set(dataparams.keys()).intersection(updateparams.keys()))
    UpdateArtistFromParameters(artist, updateparams, updatelist)
    return {'error': False, 'item': artist.to_json(), 'params': dataparams, 'data': updateparams}


def query_create():
    """Query source and create artist."""
    params = dict(url=request.values.get('url'))
    retdata = {'error': False, 'params': params}
    if params['url'] is None:
        return SetError(retdata, "Must include the artist URL.")
    source = BASE_SOURCE.GetArtistSource(params['url'])
    if source is None:
        return SetError(retdata, "Not a valid artist URL.")
    site_id = source.SiteId()
    ret = source.GetArtistId(params['url'])
    if ret is None:
        return SetError(retdata, "Unable to find site artist ID with URL.")
    if IsError(ret):
        return SetError(retdata, ret.message)
    site_artist_id = int(ret)
    artist = Artist.query.filter_by(site_id=site_id, site_artist_id=site_artist_id).first()
    if artist is not None:
        retdata['item'] = artist.to_json()
        return SetError(retdata, "Artist already exists.")
    artist = source.CreateArtist(site_artist_id)
    retdata['item'] = artist.to_json()
    return retdata


# #### Route functions

# ###### SHOW


@bp.route('/artists/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Artist, id)


@bp.route('/artists/<int:id>', methods=['GET'])
def show_html(id):
    artist = GetOrAbort(Artist, id)
    return render_template("artists/show.html", artist=artist)


# ###### INDEX


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
    if GetMethodRedirect(request):
        return index_html()
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('artist.new_html', **results['data']))
    return redirect(url_for('artist.show_html', id=results['item']['id']))


@bp.route('/artists.json', methods=['POST'])
def create_json():
    if GetMethodRedirect(request):
        return index_json()
    return create()


# ###### UPDATE


@bp.route('/artists/<int:id>/edit', methods=['GET'])
def edit_html(id):
    """HTML access point to update function."""
    artist = GetOrAbort(Artist, id)
    editparams = artist.to_json()
    editparams['account_string'] = '\r\n'.join(site_account.name for site_account in artist.site_accounts)
    editparams['name_string'] = '\r\n'.join(artist_name.name for artist_name in artist.names)
    editparams['webpage_string'] = '\r\n'.join((('' if webpage.active else '-') + webpage.url) for webpage in artist.webpages)
    form = GetArtistForm(**editparams)
    return render_template("artists/edit.html", form=form, artist=artist)


@bp.route('/artists/<int:id>', methods=['POST', 'PUT'])
def update_html(id):
    PutMethodCheck(request)
    artist = GetOrAbort(Artist, id)
    update(artist)
    return redirect(url_for('artist.show_html', id=artist.id))


@bp.route('/artists/<int:id>', methods=['POST', 'PUT'])
def update_json(id):
    PutMethodCheck(request)
    artist = GetOrError(Artist, id)
    if type(artist) is dict:
        return artist
    return update(artist)


# ###### MISC


@bp.route('/artists/query_create', methods=['POST'])
def query_create_html():
    """Query source and create artist."""
    results = query_create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    flash('Artist created.')
    return redirect(url_for('artist.show_html', id=results['item']['id']))


@bp.route('/artists/<int:id>/query_update', methods=['POST'])
def query_update_html(id):
    """Query source and update artist."""
    artist = GetOrAbort(Artist, id)
    source = BASE_SOURCE._Source(artist.site_id)
    updateparams = source.GetArtistData(artist.site_artist_id)
    if updateparams['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        updateparams['webpages'] += ['-' + webpage.url for webpage in artist.webpages if webpage.url not in updateparams['webpages']]
        updateparams['names'] += [artist_name.name for artist_name in artist.names if artist_name.name not in updateparams['names']]
        updateparams['site_accounts'] += [site_account.name for site_account in artist.site_accounts if site_account.name not in updateparams['site_accounts']]
    updatelist = list(updateparams.keys())
    UpdateArtistFromParameters(artist, updateparams, updatelist)
    flash("Artist updated.")
    return redirect(url_for('artist.show_html', id=id))


@bp.route('/artists/<int:id>/query_booru', methods=['POST'])
def query_booru_html(id):
    """Query booru and create/update booru relationships."""
    artist = GetOrAbort(Artist, id)
    response = BASE_SOURCE.QueryArtistBoorus(artist)
    if response['error']:
        flash(response['message'])
    else:
        flash('Artist updated.')
    return redirect(url_for('artist.show_html', id=id))
