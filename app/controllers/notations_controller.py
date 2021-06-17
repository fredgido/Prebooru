# APP\CONTROLLERS\NOTATIONS_CONTROLLER.PY

# ## PYTHON IMPORTS
import requests
from sqlalchemy.orm import selectinload
from flask import Blueprint, request, render_template, abort, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, Form
from wtforms.validators import DataRequired
from wtforms.meta import DefaultMeta

# ## LOCAL IMPORTS

from ..logical.utility import EvalBoolString, IsTruthy, IsFalsey, GetCurrentTime
from ..logical.logger import LogError
from ..models import Notation, Pool
from ..sources import base as BASE_SOURCE
from ..database import local as DBLOCAL
from .base_controller import GetSearch, ShowJson, IndexJson, IdFilter, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, GetDataParams


# ## GLOBAL VARIABLES

bp = Blueprint("notation", __name__)

# Forms

class BindNameMeta(DefaultMeta):
    def bind_field(self, form, unbound_field, options):
        if 'custom_name' in unbound_field.kwargs:
            options['name'] = unbound_field.kwargs.pop('custom_name')
        return unbound_field.bind(form=form, **options)

class CustomNameForm(Form):
    Meta = BindNameMeta

def GetNotationFrom(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class NotationForm(CustomNameForm):
        body = TextAreaField('Body', id='notation-body', custom_name='notation[body]', validators=[DataRequired()])
        pool_id = IntegerField('Pool ID', id='notation-pool-id', custom_name='notation[pool_id]')
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
    #search = GetSearch(request)
    print("Params:", params, flush=True)
    print("Search:", search, flush=True)
    q = Notation.query
    #q = IdFilter(q, search)
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q

@bp.route('/notations/new', methods=['GET'])
def new_html():
    form = GetNotationFrom()
    return render_template("notations/new.html", form=form, notation=None)

@bp.route('/notations/<int:id>/edit', methods=['GET'])
def edit_html(id):
    notation = Notation.find(id)
    if notation is None:
        abort(404)
    pool_id = notation._pools[0].pool_id if len(notation._pools) > 0 else None
    form = GetNotationFrom(body=notation.body, pool_id=pool_id)
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

@bp.route('/notations', methods=['POST'])
def create_html():
    print("create_html")
    dataparams = GetDataParams(request, 'notation')
    if 'body' not in dataparams:
        abort(405, "Must include body.")
    dataparams['pool_id'] = int(dataparams['pool_id']) if dataparams['pool_id'].isdigit() else None
    print(dataparams)
    #return redirect(url_for('notation.new_html'))
    current_time = GetCurrentTime()
    notation = Notation(body=dataparams['body'], created=current_time, updated=current_time)
    DBLOCAL.SaveData(notation)
    if dataparams['pool_id'] is not None:
        pool=Pool.find(dataparams['pool_id'])
        if pool is None:
            flash('Unable to add to pool; pool #%d does not exist.' % dataparams['pool_id'])
        pool.elements.append(notation)
        DBLOCAL.SaveData()
    return redirect(url_for('notation.show_html', id=notation.id))
