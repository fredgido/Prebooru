# APP\CONTROLLERS\ILLUSTS.PY

# ## PYTHON IMPORTS
import json
from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash
from sqlalchemy.orm import selectinload, lazyload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS

from ..logical.utility import GetCurrentTime, EvalBoolString
from ..logical.logger import LogError
from ..models import Error
from ..sources.base import GetImageSiteId, GetImageSource
from ..database import local as DBLOCAL
from ..database.illust_url_db import CreateIllustUrlFromParameters
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder, Paginate,\
    GetDataParams, CustomNameForm, ParseType, GetOrAbort, GetOrError, SetError, PutMethodCheck, UpdateColumnAttributes,\
    NullifyBlanks, CheckParamRequirements, HideInput


# ## GLOBAL VARIABLES

bp = Blueprint("error", __name__)


# ## FUNCTIONS

# #### Route helpers


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Error.query
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


# #### Route functions


# ###### SHOW/INDEX


@bp.route('/errors/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Error, id)


@bp.route('/errors/<int:id>', methods=['GET'])
def show_html(id):
    error = GetOrAbort(Error, id)
    return render_template("errors/show.html", error=error)


@bp.route('/errors.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/errors', methods=['GET'])
def index_html():
    q = index()
    errors = Paginate(q, request)
    return render_template("errors/index.html", errors=errors, error=Error())
