# APP\CONTROLLERS\ARTISTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort
from sqlalchemy.orm import selectinload, lazyload

# ## LOCAL IMPORTS

from ..models import Artist
from .base import GetSearch, ShowJson, IndexJson, IdFilter, Paginate, DefaultOrder


# ## GLOBAL VARIABLES

bp = Blueprint("artist", __name__)

# ## FUNCTIONS



@bp.route('/artists/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Artist, id)


@bp.route('/artists/<int:id>', methods=['GET'])
def show_html(id):
    artist = Artist.query.filter_by(id=id).first()
    return render_template("artists/show.html", artist=artist) if artist is not None else abort(404)


@bp.route('/artists.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/artists', methods=['GET'])
def index_html():
    q = index()
    artists = Paginate(q, request)
    return render_template("artists/index.html", artists=artists)


def index():
    search = GetSearch(request)
    print(search)
    q = Artist.query
    q = q.options(selectinload(Artist.names), selectinload(Artist.site_accounts), selectinload(Artist.webpages), lazyload(Artist.profiles))
    q = IdFilter(q, search)
    if 'site_artist_id' in search:
        q = q.filter_by(site_artist_id=search['site_artist_id'])
    if 'illust_site_illust_id' in search:
        q = q.filter(Artist.illusts.any(site_illust_id=search['illust_site_illust_id']))
    q = DefaultOrder(q)
    return q
