# APP\CONTROLLERS\ARTISTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, redirect, url_for, flash
from sqlalchemy.orm import selectinload, lazyload

# ## LOCAL IMPORTS

from ..logical.logger import LogError
from ..models import Illust, Artist
#from ..models.artist import Names, SiteAccounts
from ..sources import base as BASE_SOURCE
from .base_controller import GetSearch, ShowJson, IndexJson, IdFilter, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, GetDataParams


# ## GLOBAL VARIABLES

bp = Blueprint("artist", __name__)

# ## FUNCTIONS

def CheckDataParams(dataparams):
    if 'site_id' not in dataparams or not dataparams['site_id'].isdigit():
        return "No site ID present!"
    if 'site_artist_id' not in dataparams or not dataparams['site_artist_id'].isdigit():
        return "No site artist ID present!"


def ConvertDataParams(dataparams):
    dataparams['site_id'] = int(dataparams['site_id'])
    dataparams['site_artist_id'] = int(dataparams['site_artist_id'])


@bp.route('/artists/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Artist, id)


@bp.route('/artists/<int:id>', methods=['GET'])
def show_html(id):
    artist = Artist.query.filter_by(id=id).first()
    return render_template("artists/show.html", artist=artist) if artist is not None else abort(404)

@bp.route('/artists/<int:id>/update', methods=['GET'])
def update_html(id):
    artist = Artist.find(id)
    if artist is None:
        abort(404)
    BASE_SOURCE.UpdateArtist(artist)
    flash("Artist updated.")
    return redirect(url_for('artist.show_html', id=id))

@bp.route('/artists.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/artists', methods=['GET'])
def index_html():
    q = index()
    artists = Paginate(q, request)
    return render_template("artists/index.html", artists=artists, artist=None)


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    #search = GetSearch(request)
    print("Params:", params, flush=True)
    print("Search:", search, flush=True)
    q = Artist.query
    q = q.options(selectinload(Artist.names), selectinload(Artist.site_accounts), selectinload(Artist.webpages), lazyload(Artist.profiles))
    #q = IdFilter(q, search)
    q = SearchFilter(q, search)
    """TEMP
    if 'names' in search:
        q = q.unique_join(Names, Artist.names).filter(Names.name == search['names'])
    if 'site_accounts' in search:
        q = q.unique_join(SiteAccounts, Artist.site_accounts).filter(SiteAccounts.name == search['site_accounts'])
    #if 'site_artist_id' in search:
    #    q = q.filter_by(site_artist_id=search['site_artist_id'])
    if 'illust_site_illust_id' in search:
        #q = q.filter(Artist.illusts.any(site_illust_id=search['illust_site_illust_id']))
        q = q.unique_join(Illust).filter(Illust.site_illust_id == search['illust_site_illust_id'])
    """
    q = DefaultOrder(q, search)
    return q


@bp.route('/artists.json', methods=['post'])
def create():
    dataparams = GetDataParams(request, 'artist')
    error = CheckDataParams(dataparams)
    if error is not None:
        return {'error': True, 'message': error, 'params': dataparams}
    ConvertDataParams(dataparams)
    print(dataparams)
    #return "nothing"
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
    return {'error': False, 'artist': artist}

@bp.route('/artists/query.json', methods=['post'])
def query():
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
    return {'error': False, 'artist': artist}
