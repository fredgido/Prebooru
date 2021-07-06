# APP\CONTROLLERS\BOORUS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, redirect, url_for, flash
from sqlalchemy.orm import selectinload

# ## LOCAL IMPORTS
from ..models import Booru
from ..sources import base as BASE_SOURCE
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder


# ## GLOBAL VARIABLES


bp = Blueprint("booru", __name__)


# ## FUNCTIONS

# #### Helper functions


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    print("Params:", params, flush=True)
    print("Search:", search, flush=True)
    q = Booru.query
    q = q.options(selectinload(Booru.names), selectinload(Booru.artists).lazyload('*'))
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


# #### Route functions

# ###### SHOW/INDEX


@bp.route('/boorus/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Booru, id)


@bp.route('/boorus/<int:id>', methods=['GET'])
def show_html(id):
    booru = Booru.find(id)
    return render_template("boorus/show.html", booru=booru) if booru is not None else abort(404)


@bp.route('/boorus.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/boorus', methods=['GET'])
def index_html():
    q = index()
    boorus = Paginate(q, request)
    return render_template("boorus/index.html", boorus=boorus, booru=None)


# ###### MISC


@bp.route('/boorus/<int:id>/query_update', methods=['GET'])
def query_update_html(id):
    booru = Booru.find(id)
    if booru is None:
        abort(404)
    BASE_SOURCE.UpdateBooru(booru)
    flash("Booru updated.")
    return redirect(url_for('booru.show_html', id=id))
