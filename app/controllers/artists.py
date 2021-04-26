# APP\CONTROLLERS\ARTISTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request


# ## LOCAL IMPORTS

from ..models import Artist
from .base import GetSearch, ShowJson, IndexJson, IdFilter


# ## GLOBAL VARIABLES

bp = Blueprint("artist", __name__)

# ## FUNCTIONS


@bp.route('/artists/<int:id>.json', methods=['GET'])
def show(id):
    return ShowJson(Artist, id)


@bp.route('/artists.json', methods=['GET'])
def index():
    search = GetSearch(request)
    print(search)
    q = Artist.query
    q = IdFilter(q, search)
    return IndexJson(q, request)
