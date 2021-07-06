# APP\CONTROLLERS\ILLUSTS.PY

# ## PYTHON IMPORTS
import json
from flask import Blueprint, request, render_template, abort, jsonify, redirect, url_for, flash
from sqlalchemy.orm import selectinload, lazyload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS

from ..logical.utility import GetCurrentTime, EvalBoolString
from ..logical.logger import LogError
from ..models import IllustUrl, Illust, Artist, Notation, Pool
from ..sources import base as BASE_SOURCE
from ..database import local as DBLOCAL
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder, Paginate, GetDataParams, CustomNameForm, ParseType


# ## GLOBAL VARIABLES

bp = Blueprint("illust", __name__)

# Forms

def GetIllustForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class IllustForm(CustomNameForm):
        site_id = SelectField('Site', choices=[('1', 'Pixiv'), ('3', 'Twitter')], id='illust-site-id', custom_name='illust[site_id]', validators=[DataRequired()])
        site_illust_id = IntegerField('Site Illust ID', id='illust-site-illust-id', custom_name='illust[site_illust_id]', validators=[DataRequired()])
        artist_id = IntegerField('Artist ID', id='illust-artist-id', custom_name='illust[artist_id]', validators=[DataRequired()])
        pages = IntegerField('Pages', id='illust-pages', custom_name='illust[pages]')
        score = IntegerField('Score', id='illust-score', custom_name='illust[score]')
        active = BooleanField('Active', id='illust-active', custom_name='illust[active]')
        tag_string = StringField('Tag string', id='illust-tag-string', custom_name='illust[tag_string]')
        commentary = TextAreaField('Commentary', id='illust-commentary', custom_name='illust[commentary]')
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

def HTMLIllustExistenceCheck(id):
    illust = Illust.find(id)
    if illust is None:
        abort(404, "Illust not found.")
    return illust

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

@bp.route('/illusts/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Illust, id)


@bp.route('/illusts/<int:id>', methods=['GET'])
def show_html(id):
    illust = Illust.query.filter_by(id=id).first()
    return render_template("illusts/show.html", illust=illust) if illust is not None else abort(404)

@bp.route('/illusts/<int:id>/pools.json', methods=['GET'])
def show_pools_json(id):
    illust = Illust.find(id)
    pools = [pool.to_json() for pool in illust.pools]
    return jsonify(pools)


@bp.route('/illusts.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)

@bp.route('/illusts/pools.json', methods=['GET'])
def index_pools_json():
    illusts = index().all()
    retvalue = {}
    for illust in illusts:
        id_str = str(illust.id)
        pools = [pool.to_json() for pool in illust.pools]
        retvalue[id_str] = pools
    return retvalue

@bp.route('/illusts', methods=['GET'])
def index_html():
    q = index()
    illusts = Paginate(q, request)
    return render_template("illusts/index.html", illusts=illusts)


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    print("Params:", params, flush=True)
    print("Search:", search, flush=True)
    q = Illust.query
    q = q.options(selectinload(Illust.site_data), lazyload('*'))
    q = SearchFilter(q, search)
    #if 'site_illust_id' in search:
    #    q = q.filter_by(site_illust_id=search['site_illust_id'])
    """
    if 'url_site_id' in search:
        #q = q.filter(Illust.urls.any(site_id=search['url_site_id']))
        q = q.unique_join(IllustUrl).filter(IllustUrl.site_id == search['url_site_id'])
    """
    q = DefaultOrder(q, search)
    return q

@bp.route('/illusts/new', methods=['GET'])
def new_html():
    site_id = request.args.get('site_id', type=int)
    artist_id = request.args.get('artist_id', type=int)
    form = GetIllustForm(site_id=site_id, artist_id=artist_id)
    return render_template("illusts/new.html", form=form, illust=None)

@bp.route('/illusts/<int:id>/edit', methods=['GET'])
def edit_html(id):
    illust = Illust.find(id)
    if illust is None:
        abort(404)
    form = GetIllustForm(site_id=illust.site_id, site_illust_id=illust.site_illust_id, artist_id=illust.artist_id, pages=illust.pages, score=illust.score, active=illust.active)
    return render_template("illusts/edit.html", form=form, illust=illust)

@bp.route('/illusts/<int:id>/update', methods=['GET'])
def update_html(id):
    illust = Illust.find(id)
    if illust is None:
        abort(404)
    BASE_SOURCE.UpdateIllust(illust)
    flash("Illust updated.")
    return redirect(url_for('illust.show_html', id=id))

@bp.route('/illusts', methods=['POST'])
def create_html():
    dataparams = GetDataParams(request, 'illust')
    createparams = ConvertCreateParams(dataparams)
    print(dataparams, createparams, request.values)
    error = CheckCreateParams(createparams)
    if error is not None:
        return {'error': True, 'message': error, 'params': createparams}
    artist = Artist.find(createparams['artist_id'])
    if artist is None:
        return {'error': True, 'message': "Artist does not exist.", 'params': createparams}
    illust = Illust.query.filter_by(site_id=createparams['site_id'], site_illust_id=createparams['site_illust_id']).first()
    if illust is not None:
        return {'error': True, 'message': "Illust already exists.", 'params': createparams, 'illust': illust.to_json()}
    #return createparams
    illust = BASE_SOURCE.CreateDBIllustFromParams(createparams)
    return redirect(url_for('illust.show_html', id=illust.id))

@bp.route('/illusts.json', methods=['POST'])
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


@bp.route('/illusts/<int:id>/illust_urls/new', methods=['GET'])
def new_illust_url_html(id):
    illust = Illust.find(id)
    if illust is None:
        abort(404)
    form = GetIllustUrlForm()
    return render_template("illusts/new_illust_url.html", form=form, illust=illust)

@bp.route('/illusts/<int:id>/illust_urls', methods=['POST'])
def create_illust_url_html(id):
    illust = Illust.find(id)
    if illust is None:
        abort(404)
    dataparams = GetDataParams(request, 'illust_url')
    createparams = ConvertCreateUrlParams(dataparams)
    print(dataparams, createparams, request.values)
    error = CheckCreateUrlParams(createparams)
    if error is not None:
        return {'error': True, 'message': error, 'params': createparams}
    createparams['illust_id'] = illust.id
    illust_url = BASE_SOURCE.CreateDBIllustUrlFromParams(createparams, illust)
    return redirect(url_for('illust.show_html', id=illust.id))


@bp.route('/illusts/<int:id>/notation.json', methods=['POST'])
def add_notation_json(id):
    illust = Illust.find(id)
    if illust is None:
        return {'error': True, 'message': "Illust #%d not found." % id}
    dataparams = GetDataParams(request, 'illust')
    if 'notation' not in dataparams:
        return {'error': True, 'message': "Must include notation.", 'params': dataparams}
    current_time = GetCurrentTime()
    note = Notation(body=dataparams['notation'], created=current_time, updated=current_time)
    DBLOCAL.SaveData(note)
    illust.notations.append(note)
    DBLOCAL.SaveData()
    return {'error': False, 'note': note, 'illust': illust, 'params': dataparams}

@bp.route('/illusts/<int:id>/pools/new', methods=['GET'])
def add_new_pool_html(id):
    illust = HTMLIllustExistenceCheck(id)
    form = GetAddPoolIllustForm()
    return render_template("illusts/add_pool.html", form=form, illust=illust)

@bp.route('/illusts/<int:id>/pools', methods=['POST'])
def add_pool_html(id):
    illust = HTMLIllustExistenceCheck(id)
    dataparams = GetDataParams(request, 'illust')
    pool_id = ParseType(dataparams, 'pool_id', int)
    if pool_id is None:
        flash("Must include valid pool ID.", 'error')
        redirect(url_for('illust.add_new_pool_html', id=id))
    pool = Pool.find(pool_id)
    if pool is None:
        flash("Pool #%d not found." % pool_id, 'error')
        redirect(url_for('illust.add_new_pool_html', id=id))
    pool_ids = [pool.id for pool in illust.pools]
    if pool.id in pool_ids:
        flash("Illust #%d already in pool #%d." % (illust.id, pool.id), 'error')
        redirect(url_for('illust.add_new_pool_html', id=id))
    pool.updated = GetCurrentTime()
    pool.elements.append(illust)
    DBLOCAL.SaveData()
    return redirect(url_for('illust.show_html', id=id))
