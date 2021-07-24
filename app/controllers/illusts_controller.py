# APP\CONTROLLERS\ILLUSTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash
from sqlalchemy.orm import selectinload, lazyload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..models import Illust, Artist
from ..sources.base import GetSourceById
from ..database.illust_db import CreateIllustFromParameters, UpdateIllustFromParameters
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder,\
    Paginate, GetDataParams, CustomNameForm, GetOrAbort, GetOrError, SetError, HideInput, IntOrBlank,\
    NullifyBlanks, SetDefault, CheckParamRequirements, ParseArrayParameter, ParseBoolParameter,\
    PutMethodCheck, GetMethodRedirect


# ## GLOBAL VARIABLES

bp = Blueprint("illust", __name__)

CREATE_REQUIRED_PARAMS = ['artist_id', 'site_id', 'site_illust_id']
VALUES_MAP = {
    'tags': 'tags',
    'tag_string': 'tags',
    'commentaries': 'commentaries',
    'commentary': 'commentaries',
    'retweets': 'retweets',
    'replies': 'replies',
    'quotes': 'quotes',
    **{k: k for k in Artist.__table__.columns.keys()},
}

# Forms


def GetIllustForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class IllustForm(CustomNameForm):
        artist_id = IntegerField('Artist ID', id='illust-illust-id', custom_name='illust[artist_id]', validators=[DataRequired()])
        site_id = SelectField('Site', choices=[("", ""), ('1', 'Pixiv'), ('3', 'Twitter')], id='illust-site-id', custom_name='illust[site_id]', validators=[DataRequired()], coerce=IntOrBlank)
        site_illust_id = IntegerField('Site Illust ID', id='illust-site-illust-id', custom_name='illust[site_illust_id]', validators=[DataRequired()])
        site_created = StringField('Site Created', id='illust-site-created', custom_name='illust[site_created]', description='Format must be ISO8601 timestamp (e.g. 2021-05-24T04:46:51).')
        site_updated = StringField('Site Updated', id='illust-site-updated', custom_name='illust[site_updated]', description='Format must be ISO8601 timestamp (e.g. 2021-05-24T04:46:51).')
        site_uploaded = StringField('Site Uploaded', id='illust-site-uploaded', custom_name='illust[site_uploaded]', description='Format must be ISO8601 timestamp (e.g. 2021-05-24T04:46:51).')
        pages = IntegerField('Pages', id='illust-pages', custom_name='illust[pages]')
        score = IntegerField('Score', id='illust-score', custom_name='illust[score]')
        bookmarks = IntegerField('Bookmarks', id='illust-bookmarks', custom_name='illust[bookmarks]')
        retweets = IntegerField('Retweets', id='illust-retweets', custom_name='illust[retweets]')
        replies = IntegerField('Replies', id='illust-replies', custom_name='illust[replies]')
        quotes = IntegerField('Quotes', id='illust-quotes', custom_name='illust[quotes]')
        tag_string = TextAreaField('Tag string', id='illust-tag-string', custom_name='illust[tag_string]', description="Separated by whitespace.")
        title = StringField('Title', id='illust-title', custom_name='illust[title]')
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

def UniquenessCheck(dataparams, illust):
    site_id = dataparams['site_id'] if 'site_id' in dataparams else illust.site_id
    site_illust_id = dataparams['site_illust_id'] if 'site_illust_id' in dataparams else illust.site_illust_id
    if site_id != illust.site_id or site_illust_id != illust.site_illust_id:
        return Illust.query.filter_by(site_id=site_id, site_illust_id=site_illust_id).first()


def ConvertDataParams(dataparams):
    params = GetIllustForm(**dataparams).data
    params['tags'] = ParseArrayParameter(dataparams, 'tags', 'tag_string', r'\s')
    params['active'] = ParseBoolParameter(dataparams, 'active')
    params['commentaries'] = params['profile']
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
    if GetMethodRedirect(request):
        return index_html()
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('illust.new_html', **results['data']))
    return redirect(url_for('illust.show_html', id=results['item']['id']))


@bp.route('/illusts.json', methods=['POST'])
def create_json():
    if GetMethodRedirect(request):
        return index_json()
    return create()


# ###### UPDATE

@bp.route('/illusts/<int:id>/edit', methods=['GET'])
def edit_html(id):
    """HTML access point to update function."""
    illust = GetOrAbort(Illust, id)
    form = GetIllustForm(site_id=illust.site_id, site_illust_id=illust.site_illust_id, artist_id=illust.artist_id, pages=illust.pages, score=illust.score, active=illust.active)
    return render_template("illusts/edit.html", form=form, illust=illust)


@bp.route('/illusts/<int:id>', methods=['POST', 'PUT'])
def update_html(id):
    PutMethodCheck(request)
    illust = GetOrAbort(Illust, id)
    results = update(illust)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('illust.edit_html', id=illust.id))
    return redirect(url_for('illust.show_html', id=illust.id))


@bp.route('/illusts/<int:id>', methods=['POST', 'PUT'])
def update_json(id):
    PutMethodCheck(request)
    illust = GetOrError(Illust, id)
    if type(illust) is dict:
        return illust
    return update(illust)


# ## POOLS

# ########## SHOW/INDEX

# Make a POOL_ELEMENTS_CONTROLLER instead of having the following

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
