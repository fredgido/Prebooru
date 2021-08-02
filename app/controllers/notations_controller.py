# APP\CONTROLLERS\NOTATIONS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from wtforms import TextAreaField, IntegerField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..models import Notation
from ..database.notation_db import CreateNotationFromParameters, UpdateNotationFromParameters, AppendToItem, DeleteNotation
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, GetDataParams, CustomNameForm,\
    GetOrAbort, HideInput, NullifyBlanks, CheckParamRequirements, SetError


# ## GLOBAL VARIABLES

bp = Blueprint("notation", __name__)

CREATE_REQUIRED_PARAMS = ['body']
VALUES_MAP = {
    **{k: k for k in Notation.__table__.columns.keys()},
}

APPEND_KEYS = ['pool_id', 'artist_id', 'illust_id', 'post_id']


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

# #### Helper functions

def AppendNewItems(notation, dataparams):
    retdata = {'error': False}
    append_key = [key for key in APPEND_KEYS if key in dataparams and dataparams[key] is not None]
    if len(append_key) > 1:
        return SetError(retdata, "May only append using the ID of a single entity; multiple values found: %s" % append_key)
    if len(append_key) == 1:
        return AppendToItem(notation, append_key[0], dataparams)
    return retdata


# #### Form functions

def NonGeneralFormCheck(form):
    if any(getattr(form, key).data is not None for key in APPEND_KEYS):
        for key in APPEND_KEYS:
            HideInput(form, key)


# #### Param functions

def ConvertDataParams(dataparams):
    params = GetNotationForm(**dataparams).data
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    return ConvertDataParams(dataparams)


def ConvertUpdateParams(dataparams):
    updateparams = ConvertDataParams(dataparams)
    updatelist = [VALUES_MAP[key] for key in dataparams if key in VALUES_MAP]
    updateparams = {k: v for (k, v) in updateparams.items() if k in updatelist}
    return updateparams


# #### Route auxiliary functions

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Notation.query
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


def create():
    dataparams = GetDataParams(request, 'notation')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    notation = CreateNotationFromParameters(createparams)
    retdata.update(AppendNewItems(notation, createparams))
    retdata['item'] = notation.to_json()
    return retdata


def update(notation):
    dataparams = GetDataParams(request, 'notation')
    updateparams = ConvertUpdateParams(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    UpdateNotationFromParameters(notation, updateparams)
    if notation.append_type is None:
        retdata.update(AppendNewItems(notation, updateparams))
    retdata['item'] = notation.to_json()
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/notations/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Notation, id)


@bp.route('/notations/<int:id>', methods=['GET'])
def show_html(id):
    notation = GetOrAbort(Notation, id)
    return render_template("notations/show.html", notation=notation)


# ###### INDEX

@bp.route('/notations.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/notations', methods=['GET'])
def index_html():
    q = index()
    notations = Paginate(q, request)
    return render_template("notations/index.html", notations=notations, notation=Notation())


# ###### CREATE

@bp.route('/notations/new', methods=['GET'])
def new_html():
    form = GetNotationForm(**request.args)
    NonGeneralFormCheck(form)
    return render_template("notations/new.html", form=form, notation=Notation())


@bp.route('/notations', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('notation.new_html', **results['data']))
    return redirect(url_for('notation.show_html', id=results['item']['id']))


@bp.route('/notations.json', methods=['POST'])
def create_json():
    return create()


# ###### UPDATE

@bp.route('/notations/<int:id>/edit', methods=['GET'])
def edit_html(id):
    notation = GetOrAbort(Notation, id)
    editparams = notation.to_json()
    append_type = notation.append_type
    if append_type is not None:
        append_key = append_type + '_id'
        append_id = notation.append_id(append_type)
        editparams[append_key] = append_id
    form = GetNotationForm(**editparams)
    NonGeneralFormCheck(form)
    return render_template("notations/edit.html", form=form, notation=notation)


@bp.route('/notations/<int:id>', methods=['PUT'])
def update_html(id):
    notation = GetOrAbort(Notation, id)
    results = update(notation)
    if results['error']:
        flash(results['message'], 'error')
    return redirect(url_for('notation.show_html', id=notation.id))


# ####DELETE

@bp.route('/notations/<int:id>', methods=['DELETE'])
def delete_html(id):
    notation = GetOrAbort(Notation, id)
    DeleteNotation(notation)
    flash("Notation deleted.")
    return redirect(url_for('notation.index_html'))
