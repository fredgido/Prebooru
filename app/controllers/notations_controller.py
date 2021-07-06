# APP\CONTROLLERS\NOTATIONS_CONTROLLER.PY

# ## PYTHON IMPORTS
import requests
from sqlalchemy.orm import selectinload
from flask import Blueprint, request, render_template, abort, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS

from ..logical.utility import EvalBoolString, IsTruthy, IsFalsey, GetCurrentTime
from ..logical.logger import LogError
from ..models import Notation, Pool, Artist, Illust, Post
from ..sources import base as BASE_SOURCE
from ..database import local as DBLOCAL
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, GetDataParams, CustomNameForm


# ## GLOBAL VARIABLES

bp = Blueprint("notation", __name__)

# Forms

def GetNotationForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class NotationForm(CustomNameForm):
        body = TextAreaField('Body', id='notation-body', custom_name='notation[body]', validators=[DataRequired()])
        pool_id = IntegerField('Pool ID', id='notation-pool-id', custom_name='notation[pool_id]')
        artist_id = IntegerField('Artist ID', id='notation-artist-id', custom_name='notation[artist_id]')
        illust_id = IntegerField('Illust ID', id='notation-illust-id', custom_name='notation[illust_id]')
        post_id = IntegerField('Post ID', id='notation-pool-id', custom_name='notation[post_id]')
    return NotationForm(**kwargs)

# ## FUNCTIONS

@bp.route('/notations/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Notation, id)


@bp.route('/notations/<int:id>', methods=['GET'])
def show_html(id):
    notation = Notation.find(id)
    return render_template("notations/show.html", notation=notation) if notation is not None else abort(404)

@bp.route('/notations.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/notations', methods=['GET'])
def index_html():
    q = index()
    notations = Paginate(q, request)
    return render_template("notations/index.html", notations=notations)


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    print("Params:", params, flush=True)
    print("Search:", search, flush=True)
    q = Notation.query
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q

@bp.route('/notations/new', methods=['GET'])
def new_html():
    pool_id=request.args.get('pool_id', type=int)
    artist_id=request.args.get('artist_id', type=int)
    illust_id=request.args.get('illust_id', type=int)
    post_id=request.args.get('post_id', type=int)
    print(request.args, pool_id, artist_id, illust_id, post_id)
    form = GetNotationForm(pool_id=pool_id, artist_id=artist_id, illust_id=illust_id, post_id=post_id)
    return render_template("notations/new.html", form=form, notation=None)

@bp.route('/notations/<int:id>/edit', methods=['GET'])
def edit_html(id):
    notation = Notation.find(id)
    if notation is None:
        abort(404)
    pool_id = notation._pools[0].pool_id if len(notation._pools) > 0 else None
    form = GetNotationForm(body=notation.body, pool_id=pool_id)
    return render_template("notations/edit.html", form=form, notation=notation)

@bp.route('/notations/<int:id>', methods=['POST','PUT'])
def update_html(id):
    print("update_html", request.method, request.values.get('_method'))
    if request.method == 'POST' and request.values.get('_method', default='').upper() != 'PUT':
        abort(405)
    notation = Notation.find(id)
    if notation is None:
        abort(404)
    is_dirty = False
    dataparams = GetDataParams(request, 'notation')
    print(dataparams)
    if 'body' in dataparams and notation.body != dataparams['body']:
        print("Updating body.")
        notation.body = dataparams['body']
        is_dirty = True
    if is_dirty:
        print("Changes detected.")
        notation.updated = GetCurrentTime()
        DBLOCAL.SaveData()
    return redirect(url_for('notation.show_html', id=notation.id))

APPEND_KEYS = ['pool_id', 'artist_id', 'illust_id', 'post_id']
ID_MODEL_DICT = {
    'pool_id': Pool,
    'artist_id': Artist,
    'illust_id': Illust,
    'post_id': Post,
}

def FormatParams(dataparams):
    for key in APPEND_KEYS:
        dataparams[key] = int(dataparams[key]) if (key in dataparams) and dataparams[key].isdigit() else None


@bp.route('/notations', methods=['POST'])
def create_html():
    print("create_html")
    dataparams = GetDataParams(request, 'notation')
    if 'body' not in dataparams:
        abort(405, "Must include body.")
    FormatParams(dataparams)
    print(dataparams)
    append_key = [key for key in APPEND_KEYS if dataparams[key] is not None]
    if len(append_key) > 1:
        flash("May only append using the ID of a single entity; multiple values found: %s" % append_key, 'error')
        # Figure out how to send the data params back to the new form
        return redirect(url_for('notation.new_html'))
    current_time = GetCurrentTime()
    notation = Notation(body=dataparams['body'], created=current_time, updated=current_time)
    DBLOCAL.SaveData(notation)
    if len(append_key) == 1:
        append_key = append_key[0]
        model = ID_MODEL_DICT[append_key]
        item=model.find(dataparams[append_key])
        table_name = model.__table__.name
        if item is None:
            flash('Unable to add to %s; %s #%d does not exist.' % (mdataparams['pool_id'], table_name, table_name), 'error')
        else:
            if table_name == 'pool':
                item.elements.append(notation)
            else:
                item.notations.append(notation)
            DBLOCAL.SaveData()
    return redirect(url_for('notation.show_html', id=notation.id))
