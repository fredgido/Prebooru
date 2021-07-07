# APP\CONTROLLERS\UPLOADS.PY

# ## PYTHON IMPORTS
import requests
from sqlalchemy.orm import selectinload
from flask import Blueprint, request, render_template, abort, redirect, url_for, flash
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS

from ..logical.utility import EvalBoolString, IsTruthy, IsFalsey
from ..logical.logger import LogError
from ..models import Upload, Post, IllustUrl
from ..sources import base as BASE_SOURCE
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, CustomNameForm, GetDataParams, ParseType


# ## GLOBAL VARIABLES

bp = Blueprint("upload", __name__)

# ## FUNCTIONS

def GetUploadForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class UploadForm(CustomNameForm):
        illust_url_id = IntegerField('Illust URL ID', id='upload-illust-url-id', custom_name='upload[illust_url_id]', validators=[DataRequired()])
        media_filepath = StringField('Media filepath', id='illust-media-filepath', custom_name='upload[media_filepath]', validators=[DataRequired()])
        sample_filepath = StringField('Sample filepath', id='illust-sample-filepath', custom_name='upload[sample_filepath]')
    return UploadForm(**kwargs)

#    Auxiliary


def CheckParams(request):
    messages = []
    if request.values.get('url') is not None:
        return
    if request.values.get('media') is not None and request.values.get('url_id') is not None:
        return
    return "No URL or media information present!"

def ConvertCreateParams(dataparams):
    params = {}
    params['illust_url_id'] = ParseType(dataparams, 'illust_url_id', int)
    params['media_filepath'] = dataparams['media_filepath'] or None
    params['sample_filepath'] = dataparams['sample_filepath'] or None
    return params

def CheckCreateParams(dataparams):
    if dataparams['illust_url_id'] is None:
        return "No illust URL ID present!"
    if dataparams['media_filepath'] is None:
        return "No media filepath present!"

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
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    print("Params:", params, flush=True)
    print("Search:", search, flush=True)
    q = Upload.query
    q = q.options(selectinload(Upload.image_urls), selectinload(Upload.posts).lazyload(Post.illust_urls),selectinload(Upload.errors))
    q = SearchFilter(q, search)
    #if 'request_url' in search:
    #    q = q.filter_by(request_url=search['request_url'])
    #if 'status' in search:
    #    q = q.filter_by(status=search['status'])
    """
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
    """
    q = DefaultOrder(q, search)
    return q


@bp.route('/uploads/new', methods=['GET'])
def new_html():
    illust_url_id = request.args.get('illust_url_id', type=int)
    if illust_url_id is not None:
        illust_url = IllustUrl.find(illust_url_id)
        if illust_url is None:
            flash("Illust URL #%d does not exist.", 'error')
            illust_url_id = None
    form = GetUploadForm(illust_url_id=illust_url_id)
    return render_template("uploads/new.html", form=form, upload=None, illust_url=illust_url)

@bp.route('/uploads', methods=['POST'])
def create_html():
    dataparams = GetDataParams(request, 'upload')
    createparams = ConvertCreateParams(dataparams)
    print(dataparams, createparams, request.values)
    error = CheckCreateParams(createparams)
    if error is not None:
        return {'error': True, 'message': error, 'params': createparams}
    upload_results = BASE_SOURCE.CreateFileUpload(createparams['media_filepath'], createparams['sample_filepath'], createparams['illust_url_id'])
    if upload_results['error']:
        flash(upload_results['message'], 'error')
        form = GetUploadForm(**createparams)
        return render_template("uploads/new.html", form=form, upload=None)
    try:
        requests.get('http://127.0.0.1:4000/check_uploads', timeout=2)
    except Exception as e:
        print("Unable to contact worker:", e)
        flash("Unable to contact worker.")
    return redirect(url_for('upload.show_html', id=upload_results['data'].id))

@bp.route('/uploads.json', methods=['POST'])
def create_json():
    error = CheckParams(request)
    if error is not None:
        return {'error': error}
    request_url = request.values.get('url')
    referrer_url = request.values.get('ref')
    media_filepath = request.values.get('media')
    sample_filepath = request.values.get('sample')
    illust_url_id = request.values.get('url_id', type=int)
    image_urls = request.values.getlist('image_urls[]')
    force = request.values.get('force', type=EvalBoolString)
    print("Create upload:", request_url, referrer_url, media_filepath, sample_filepath, illust_url_id, image_urls, force)
    try:
        if request_url is not None:
            upload = BASE_SOURCE.CreateUpload(request_url, referrer_url, image_urls, force)
        else:
            upload = BASE_SOURCE.CreateFileUpload(media_filepath, sample_filepath, illust_url_id)
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
