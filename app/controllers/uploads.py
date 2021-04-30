# APP\CONTROLLERS\UPLOADS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort


# ## LOCAL IMPORTS

from app.logical.utility import EvalBoolString
from ..models import Upload
from ..sources import base as BASE_SOURCE
from .base import GetSearch, ShowJson, IndexJson, IdFilter, Paginate, DefaultOrder


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


@bp.route('/uploads/<int:id><string:type>')
def show(id,type):
    if type == '.json':
        return ShowJson(Upload, id)
    abort(404)


@bp.route('/uploads<string:type>', methods=['GET'])
def index(type):
    search = GetSearch(request)
    print(search)
    q = Upload.query
    q = IdFilter(q, search)
    q = DefaultOrder(q)
    if 'request_url' in search:
        q = q.filter_by(request_url=search['request_url'])
    if type == '.json':
        return IndexJson(q, request)
    elif type == '' or type == '.html':
        return render_template("uploads/index.html", uploads=Paginate(q, request))
    abort(404)


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
    print("Create upload:", force, request.values)
    try:
        return BASE_SOURCE.CreateUpload(request_url, referrer_url, image_urls, user_id, force)
    except Exception as e:
        print("Database exception!", e)
        request.environ.get('werkzeug.server.shutdown')()
        return "quitting"
