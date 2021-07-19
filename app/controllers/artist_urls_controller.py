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
from ..models import Illust, Artist, ArtistUrl, Notation, Pool, IllustUrl
from ..sources import base as BASE_SOURCE
from ..sources.base import GetImageSiteId, GetImageSource
from ..database import local as DBLOCAL
from ..database.illust_url_db import CreateIllustUrlFromParameters
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder, Paginate,\
    GetDataParams, CustomNameForm, ParseType, GetOrAbort, GetOrError, SetError, PutMethodCheck, UpdateColumnAttributes,\
    NullifyBlanks, CheckParamRequirements, HideInput


# ## GLOBAL VARIABLES

bp = Blueprint("artist_url", __name__)


# ## FUNCTIONS

# #### Route helpers


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = ArtistUrl.query
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


# #### Route functions


# ###### SHOW/INDEX


@bp.route('/artist_urls/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(ArtistUrl, id)


@bp.route('/artist_urls/<int:id>', methods=['GET'])
def show_html(id):
    artist_url = GetOrAbort(ArtistUrl, id)
    return render_template("artist_urls/show.html", artist_url=artist_url)


@bp.route('/artist_urls.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/artist_urls', methods=['GET'])
def index_html():
    q = index()
    artist_urls = Paginate(q, request)
    return render_template("artist_urls/index.html", artist_urls=artist_urls, artist_url=ArtistUrl())
