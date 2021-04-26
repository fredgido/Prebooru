# APP\CONTROLLERS\UPLOADS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request


# ## LOCAL IMPORTS

from app.logical.utility import EvalBoolString
from ..models import Upload
from ..sources import base as BASE_SOURCE
from .base import GetSearch, ShowJson, IndexJson, IdFilter


# ## GLOBAL VARIABLES

bp = Blueprint("upload", __name__)

# ## FUNCTIONS

#    Auxiliary


def CheckParams(request):
    user_id = request.values.get('user_id')
    if user_id is None or not user_id.isdigit():
        return "No user ID present!"
    if request.values.get('url') is None:
        return "No URL present!"


#   Routes


@bp.route('/uploads/<int:id>.json')
def show(id):
    return ShowJson(Upload, id)


@bp.route('/uploads.json', methods=['GET'])
def index():
    search = GetSearch(request)
    print(search)
    q = Upload.query
    q = IdFilter(q, search)
    if 'request_url' in search:
        q = q.filter_by(request_url=search['request_url'])
    return IndexJson(q, request)


@bp.route('/uploads.json', methods=['POST'])
def create():
    error = CheckParams(request)
    if error is not None:
        return {'error': error}
    user_id = int(request.values['user_id'])
    request_url = request.values['url']
    referrer_url = request.values.get('ref')
    image_urls = request.values.getlist('image_urls[]')
    force = request.values.get('force', type=EvalBoolString)
    print(force, request.values)
    return BASE_SOURCE.CreateUpload(request_url, referrer_url, image_urls, user_id, force)
