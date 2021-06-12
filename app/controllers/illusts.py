# APP\CONTROLLERS\ILLUSTS.PY

# ## PYTHON IMPORTS
import json
from flask import Blueprint, request, render_template, abort
from sqlalchemy.orm import selectinload, lazyload


# ## LOCAL IMPORTS

from ..logical.logger import LogError
from ..models import IllustUrl, Illust, Artist
from ..sources import base as BASE_SOURCE
from .base import GetSearch, ShowJson, IndexJson, IdFilter, DefaultOrder, Paginate, GetDataParams


# ## GLOBAL VARIABLES

bp = Blueprint("illust", __name__)

# ## FUNCTIONS


def CheckDataParams(dataparams):
    if 'site_id' not in dataparams or not dataparams['site_id'].isdigit():
        return "No site ID present!"
    if 'site_illust_id' not in dataparams or not dataparams['site_illust_id'].isdigit():
        return "No site illust ID present!"
    if 'site_artist_id' not in dataparams or not dataparams['site_artist_id'].isdigit():
        return "No site artist ID present!"


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


@bp.route('/illusts/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Illust, id)


@bp.route('/illusts/<int:id>', methods=['GET'])
def show_html(id):
    illust = Illust.query.filter_by(id=id).first()
    return render_template("illusts/show.html", illust=illust) if illust is not None else abort(404)


@bp.route('/illusts.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/illusts', methods=['GET'])
def index_html():
    q = index()
    illusts = Paginate(q, request)
    return render_template("illusts/index.html", illusts=illusts)


def index():
    search = GetSearch(request)
    print(search)
    q = Illust.query
    q = q.options(selectinload(Illust.site_data), lazyload('*'))
    q = IdFilter(q, search)
    if 'site_illust_id' in search:
        q = q.filter_by(site_illust_id=search['site_illust_id'])
    if 'url_site_id' in search:
        #q = q.filter(Illust.urls.any(site_id=search['url_site_id']))
        q = q.unique_join(IllustUrl).filter(IllustUrl.site_id == search['url_site_id'])
    q = DefaultOrder(q, search)
    return q

@bp.route('/illusts/<int:id>/update', methods=['GET'])
def update_html(id):
    illust = Illust.find(id)
    if illust is None:
        abort(404)
    BASE_SOURCE.UpdateIllust(illust)
    return redirect(url_for('illust.show_html', id=id))

@bp.route('/illusts.json', methods=['post'])
def create():
    dataparams = GetDataParams(request, 'illust')
    error = CheckDataParams(dataparams)
    if error is not None:
        return {'error': True, 'message': error, 'params': dataparams}
    ConvertDataParams(dataparams)
    print(dataparams)
    illust = Illust.query.filter_by(site_id=dataparams['site_id'], site_illust_id=dataparams['site_illust_id']).first()
    if illust is not None:
        return {'error': True, 'message': "Illust already exists.", 'params': dataparams, 'illust': illust}
    artist = Artist.query.filter_by(site_id=dataparams['site_id'], site_artist_id=dataparams['site_artist_id']).first()
    if artist is None:
        return {'error': True, 'message': "Artist does not exist.", 'params': dataparams}
    #return dataparams

    dataparams['artist_id'] = artist.id
    try:
        illust = BASE_SOURCE.CreateDBIllustFromParams(dataparams)
    except Exception as e:
        print("Database exception!", e)
        LogError('controllers.artists.create', "Unhandled exception occurred creating artist: %s" % (str(e)))
        request.environ.get('werkzeug.server.shutdown')()
        return {'error': True, 'message': 'Database exception! Check log file.'}
    illust_json = illust.to_json() if illust is not None else illust
    return {'error': False, 'illust': illust_json}
