# APP\CONTROLLERS\ILLUSTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request


# ## LOCAL IMPORTS

from ..models import Illust
from .base import GetSearch, ShowJson, IndexJson, IdFilter


# ## GLOBAL VARIABLES

bp = Blueprint("illust", __name__)

# ## FUNCTIONS


@bp.route('/illusts/<int:id>.json')
def show(id):
    return ShowJson(Illust, id)


@bp.route('/illusts.json', methods=['GET'])
def index():
    search = GetSearch(request)
    print(search)
    q = Illust.query
    q = IdFilter(q, search)
    if 'url_site_id' in search:
        Illust.query.filter(Illust.urls.any(site_id=search['site_id']))
    return IndexJson(q, request)
