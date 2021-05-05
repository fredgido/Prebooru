# APP\CONTROLLERS\ILLUSTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort
from sqlalchemy.orm import selectinload, lazyload


# ## LOCAL IMPORTS

from ..models import Illust
from .base import GetSearch, ShowJson, IndexJson, IdFilter, DefaultOrder, Paginate


# ## GLOBAL VARIABLES

bp = Blueprint("illust", __name__)

# ## FUNCTIONS


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
    if 'url_site_id' in search:
        q = q.filter(Illust.urls.any(site_id=search['url_site_id']))
    q = DefaultOrder(q)
    return q
