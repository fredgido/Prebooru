# APP\CONTROLLERS\ILLUSTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy import not_, or_
from sqlalchemy.orm import selectinload, lazyload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..models import Illust, IllustUrl, SiteData, Artist, Post, PoolIllust, PoolPost
from ..logical.utility import EvalBoolString, IsFalsey
from ..sources.base import GetSourceById, GetIllustRequiredParams
from ..database.illust_db import CreateIllustFromParameters, UpdateIllustFromParameters, UpdateIllustFromSource
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder,\
    Paginate, GetDataParams, CustomNameForm, GetOrAbort, GetOrError, SetError, HideInput, IntOrBlank,\
    NullifyBlanks, SetDefault, CheckParamRequirements, ParseArrayParameter, ParseBoolParameter

# ## GLOBAL VARIABLES

bp = Blueprint("illust", __name__)

CREATE_REQUIRED_PARAMS = ['artist_id', 'site_id', 'site_illust_id']
VALUES_MAP = {
    'tags': 'tags',
    'tag_string': 'tags',
    'commentaries': 'commentaries',
    'commentary': 'commentaries',
    **{k: k for k in SiteData.__table__.columns.keys() if k not in ['id', 'illust_id', 'type']},
    **{k: k for k in Artist.__table__.columns.keys()},
}

ILLUST_POOLS_SUBQUERY = Illust.query.join(PoolIllust, Illust._pools).filter(Illust.id == PoolIllust.illust_id).with_entities(Illust.id)
POST_POOLS_SUBQUERY = Illust.query.join(IllustUrl, Illust.urls).join(Post, IllustUrl.post).join(PoolPost, Post._pools).filter(Post.id == PoolPost.post_id).with_entities(Illust.id)

POOL_SEARCH_KEYS = ['has_pools', 'has_post_pools', 'has_illust_pools']

# Forms

def GetIllustForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class IllustForm(CustomNameForm):
        artist_id = IntegerField('Artist ID', id='illust-illust-id', custom_name='illust[artist_id]', validators=[DataRequired()], description="This is the Prebooru artist ID.")
        site_id = SelectField('Site', choices=[("", ""), ('1', 'Pixiv'), ('3', 'Twitter')], id='illust-site-id', custom_name='illust[site_id]', validators=[DataRequired()], coerce=IntOrBlank)
        site_illust_id = IntegerField('Site Illust ID', id='illust-site-illust-id', custom_name='illust[site_illust_id]', validators=[DataRequired()])
        site_created = StringField('Site Created', id='illust-site-created', custom_name='illust[site_created]', description='Format must be ISO8601 timestamp (e.g. 2021-05-24T04:46:51).')
        site_updated = StringField('Site Updated', id='illust-site-updated', custom_name='illust[site_updated]', description='Format must be ISO8601 timestamp (e.g. 2021-05-24T04:46:51).')
        site_uploaded = StringField('Site Uploaded', id='illust-site-uploaded', custom_name='illust[site_uploaded]', description='Format must be ISO8601 timestamp (e.g. 2021-05-24T04:46:51).')
        pages = IntegerField('Pages', id='illust-pages', custom_name='illust[pages]')
        score = IntegerField('Score', id='illust-score', custom_name='illust[score]')
        bookmarks = IntegerField('Bookmarks', id='illust-bookmarks', custom_name='illust[bookmarks]')
        views = IntegerField('Views', id='illust-views', custom_name='illust[views]')
        retweets = IntegerField('Retweets', id='illust-retweets', custom_name='illust[retweets]')
        replies = IntegerField('Replies', id='illust-replies', custom_name='illust[replies]')
        quotes = IntegerField('Quotes', id='illust-quotes', custom_name='illust[quotes]')
        tag_string = TextAreaField('Tag string', id='illust-tag-string', custom_name='illust[tag_string]', description="Separated by whitespace.")
        title = StringField('Title', id='illust-title', custom_name='illust[title]')
        commentary = TextAreaField('Commentary', id='illust-commentary', custom_name='illust[commentary]')
        active = BooleanField('Active', id='illust-active', custom_name='illust[active]')
    return IllustForm(**kwargs)


# ## FUNCTIONS

# #### Query functions

def PoolFilter(query, search):
    pool_search_key = next((key for key in POOL_SEARCH_KEYS if key in search), None)
    if pool_search_key is not None and EvalBoolString(search[pool_search_key]) is not None:
        if pool_search_key == 'has_pools':
            subclause = or_(Illust.id.in_(POST_POOLS_SUBQUERY), Illust.id.in_(ILLUST_POOLS_SUBQUERY))
        elif pool_search_key == 'has_post_pools':
            subclause = Illust.id.in_(POST_POOLS_SUBQUERY)
        elif pool_search_key == 'has_illust_pools':
            subclause = Illust.id.in_(ILLUST_POOLS_SUBQUERY)
        if IsFalsey(search[pool_search_key]):
            subclause = not_(subclause)
        query = query.filter(subclause)
    elif 'pool_id' in search and search['pool_id'].isdigit():
        query = query.unique_join(PoolIllust, Illust._pools).filter(PoolIllust.pool_id == int(search['pool_id']))
    return query


# #### Helper functions

def UniquenessCheck(dataparams, illust):
    site_id = dataparams['site_id'] if 'site_id' in dataparams else illust.site_id
    site_illust_id = dataparams['site_illust_id'] if 'site_illust_id' in dataparams else illust.site_illust_id
    if site_id != illust.site_id or site_illust_id != illust.site_illust_id:
        return Illust.query.filter_by(site_id=site_id, site_illust_id=site_illust_id).first()


def ConvertDataParams(dataparams):
    params = GetIllustForm(**dataparams).data
    params['tags'] = ParseArrayParameter(dataparams, 'tags', 'tag_string', r'\s')
    params['active'] = ParseBoolParameter(dataparams, 'active')
    params['commentaries'] = params['commentary']
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    createparams = ConvertDataParams(dataparams)
    SetDefault(createparams, 'tags', [])
    createparams['commentaries'] = createparams['commentary']
    return createparams


def ConvertUpdateParams(dataparams):
    updateparams = ConvertDataParams(dataparams)
    updatelist = [VALUES_MAP[key] for key in dataparams if key in VALUES_MAP]
    updateparams = {k: v for (k, v) in updateparams.items() if k in updatelist}
    return updateparams


# #### Route helpers

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    negative_search = GetParamsValue(params, 'not', True)
    q = Illust.query
    q = q.options(selectinload(Illust.site_data), selectinload(Illust.urls).selectinload(IllustUrl.post).lazyload('*'), lazyload('*'))
    q = SearchFilter(q, search, negative_search)
    q = PoolFilter(q, search)
    q = DefaultOrder(q, search)
    return q


def create():
    dataparams = GetDataParams(request, 'illust')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    illust = Artist.find(createparams['artist_id'])
    if illust is None:
        return SetError(retdata, "illust #%s not found." % dataparams['artist_id'])
    check_illust = UniquenessCheck(createparams, Illust())
    if check_illust is not None:
        retdata['item'] = check_illust.to_json()
        return SetError(retdata, "Illust already exists: %s" % check_illust.shortlink)
    illust = CreateIllustFromParameters(createparams)
    retdata['item'] = illust.to_json()
    return retdata


def update(illust):
    dataparams = GetDataParams(request, 'illust')
    updateparams = ConvertUpdateParams(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    check_illust = UniquenessCheck(updateparams, illust)
    if check_illust is not None:
        retdata['item'] = check_illust.to_json()
        return SetError(retdata, "Illust already exists: %s" % check_illust.shortlink)
    UpdateIllustFromParameters(illust, updateparams)
    retdata['item'] = illust.to_json()
    return retdata


def query_create():
    """Query source and create illust."""
    params = dict(url=request.values.get('url'))
    retdata = {'error': False, 'params': params}
    retdata.update(GetIllustRequiredParams(params['url']))
    if retdata['error']:
        return retdata
    check_illust = UniquenessCheck(retdata, Illust())
    if check_illust is not None:
        retdata['item'] = check_illust.to_json()
        return SetError(retdata, "Illust already exists: %s" % check_illust.shortlink)
    source = GetSourceById(retdata['site_id'])
    createparams = retdata['data'] = source.GetIllustData(retdata['site_illust_id'])
    if not createparams['active']:
        return SetError(retdata, "Illust post does not exist!")
    site_artist_id = source.GetArtistIdByIllustId(retdata['site_illust_id'])
    if site_artist_id is None:
        return SetError(retdata, "Unable to find site artist ID with URL.")
    artist = Artist.query.filter_by(site_id=retdata['site_id'], site_artist_id=int(site_artist_id)).first()
    if artist is None:
        return SetError(retdata, "Unable to find Prebooru artist... artist must exist before creating an illust.")
    createparams['artist_id'] = artist.id
    illust = CreateIllustFromParameters(createparams)
    retdata['item'] = illust.to_json()
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/illusts/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Illust, id)


@bp.route('/illusts/<int:id>', methods=['GET'])
def show_html(id):
    illust = GetOrAbort(Illust, id)
    return render_template("illusts/show.html", illust=illust)


# ###### INDEX

@bp.route('/illusts.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/illusts', methods=['GET'])
def index_html():
    q = index()
    illusts = Paginate(q, request)
    return render_template("illusts/index.html", illusts=illusts, illust=Illust())


# ###### CREATE

@bp.route('/illusts/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = GetIllustForm(**request.args)
    if form.artist_id.data is not None:
        illust = Artist.find(form.artist_id.data)
        if illust is None:
            flash("illust #%d not a valid illust." % form.artist_id.data, 'error')
            form.artist_id.data = None
        else:
            HideInput(form, 'artist_id', illust.id)
            HideInput(form, 'site_id', illust.site_id)
    return render_template("illusts/new.html", form=form, illust=Illust())


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
    editparams = illust.to_json()
    editparams['tag_string'] = '\r\n'.join(tag.name for tag in illust.tags)
    editparams.update({k: v for (k, v) in illust.site_data.to_json().items() if k not in ['id', 'illust_id', 'type']})
    form = GetIllustForm(**editparams)
    HideInput(form, 'artist_id', illust.id)
    HideInput(form, 'site_id', illust.site_id)
    return render_template("illusts/edit.html", form=form, illust=illust)


@bp.route('/illusts/<int:id>', methods=['PUT'])
def update_html(id):
    illust = GetOrAbort(Illust, id)
    results = update(illust)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('illust.edit_html', id=illust.id))
    return redirect(url_for('illust.show_html', id=illust.id))


@bp.route('/illusts/<int:id>', methods=['PUT'])
def update_json(id):
    illust = GetOrError(Illust, id)
    if type(illust) is dict:
        return illust
    return update(illust)


# ###### Misc

@bp.route('/illusts/query_create', methods=['POST'])
def query_create_html():
    """Query source and create illust."""
    results = query_create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    flash('Illust created.')
    return redirect(url_for('illust.show_html', id=results['item']['id']))


@bp.route('/illusts/<int:id>/query_update', methods=['POST'])
def query_update_html(id):
    illust = GetOrAbort(Illust, id)
    source = GetSourceById(illust.site_id)
    UpdateIllustFromSource(illust, source)
    flash("Illust updated.")
    return redirect(url_for('illust.show_html', id=id))
