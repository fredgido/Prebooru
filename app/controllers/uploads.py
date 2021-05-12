# APP\CONTROLLERS\UPLOADS.PY

# ## PYTHON IMPORTS
import requests
from sqlalchemy.orm import selectinload
from flask import Blueprint, request, render_template, abort


# ## LOCAL IMPORTS

from app.logical.utility import EvalBoolString, IsTruthy, IsFalsey
from app.logical.logger import LogError
from ..models import Upload, Post
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


@bp.route('/uploads/<int:id>.json')
def show_json(id):
    return ShowJson(Upload, id)


@bp.route('/uploads/<int:id>')
def show_html(id):
    upload = Upload.query.filter_by(id=id).first()
    return render_template("uploads/show.html", upload=upload) if upload is not None else abort(404)


@bp.route('/uploads.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/uploads', methods=['GET'])
def index_html():
    q = index()
    uploads = Paginate(q, request)
    return render_template("uploads/index.html", uploads=uploads)


def index():
    search = GetSearch(request)
    print(search)
    q = Upload.query
    q = q.options(selectinload(Upload.image_urls), selectinload(Upload.posts).lazyload(Post.illust_urls),selectinload(Upload.errors))
    q = IdFilter(q, search)
    q = DefaultOrder(q)
    if 'request_url' in search:
        q = q.filter_by(request_url=search['request_url'])
    if 'has_image_urls' in search:
        if IsTruthy(search['has_image_urls']):
            q = q.filter(Upload.image_urls.any())
        elif IsFalsey(search['has_image_urls']):
            q = q.filter(sqlalchemy.not_(Upload.image_urls.any()))
    if 'has_errors' in search:
        if IsTruthy(search['has_errors']):
            q = q.filter(Upload.errors.any())
        elif IsFalsey(search['has_errors']):
            q = q.filter(sqlalchemy.not_(Upload.errors.any()))
    return q


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
    print("Create upload:", force, request.values, image_urls)
    try:
        upload = BASE_SOURCE.CreateUpload(request_url, referrer_url, image_urls, user_id, force)
    except Exception as e:
        print("Database exception!", e)
        LogError('controllers.uploads.create', "Unhandled exception occurred creating upload: %s" % (str(e)))
        request.environ.get('werkzeug.server.shutdown')()
        return {'error': True, 'message': 'Database exception! Check log file.'}
    if not upload['error']:
        try:
            requests.get('http://127.0.0.1:4000/check_uploads', timeout=2)
        except Exception as e:
            print("Unable to contact worker:", e)
    return upload
