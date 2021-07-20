# APP\CONTROLLERS\UPLOADS.PY

# ## PYTHON IMPORTS
import requests
from sqlalchemy.orm import selectinload
from flask import Blueprint, request, render_template, abort, redirect, url_for, flash
from wtforms import StringField, IntegerField, TextAreaField

# ## LOCAL IMPORTS

from ..logical.utility import EvalBoolString
from ..models import Upload, Post, IllustUrl
from ..sources import base as BASE_SOURCE
from ..database.upload_db import CreateUploadFromParameters
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, CustomNameForm, GetDataParams,\
    HideInput, GetMethodRedirect, ParseStringList, NullifyBlanks, SetDefault, SetError, GetOrAbort


# ## GLOBAL VARIABLES


bp = Blueprint("upload", __name__)


# ## FUNCTIONS


def GetUploadForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class UploadForm(CustomNameForm):
        illust_url_id = IntegerField('Illust URL ID', id='upload-illust-url-id', custom_name='upload[illust_url_id]')
        media_filepath = StringField('Media filepath', id='upload-media-filepath', custom_name='upload[media_filepath]')
        sample_filepath = StringField('Sample filepath', id='upload-sample-filepath', custom_name='upload[sample_filepath]')
        request_url = StringField('Request URL', id='upload-request-url', custom_name='upload[sample_filepath]')
        image_url_string = TextAreaField('Image URLs', id='upload-image-url-string', custom_name='upload[image_url_string]', description="Separated by carriage returns.")
    return UploadForm(**kwargs)


#    Auxiliary


def ConvertDataParams(dataparams):
    params = GetUploadForm(**dataparams).data
    if 'image_urls' in dataparams:
        params['image_urls'] = dataparams['image_urls']
    elif 'image_url_string' in dataparams:
        dataparams['image_urls'] = params['image_urls'] = ParseStringList(dataparams, 'image_url_string', r'\r?\n')
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    createparams = ConvertDataParams(dataparams)
    SetDefault(createparams, 'image_urls', [])
    if createparams['illust_url_id']:
        createparams['request_url'] = None
        createparams['image_urls'] = []
    elif createparams['request_url']:
        createparams['illust_url_id'] = None
    return createparams


def CheckCreateParams(dataparams):
    if dataparams['illust_url_id'] is None and dataparams['request_url'] is None:
        return ["Must include the illust URL ID or the request URL."]
    if dataparams['illust_url_id'] and not dataparams['media_filepath']:
        return ["Must include the media filepath for file uploads."]
    return []


def GetExistingUpload(createparams):
    q = Upload.query
    if createparams['illust_url_id']:
        q = q.filter(Upload.illust_url_id == createparams['illust_url_id'])
    elif createparams['request_url']:
        q = q.filter(Upload.request_url == createparams['request_url'])
    return q.first()


# #### Route helpers


def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Upload.query
    q = q.options(selectinload(Upload.image_urls), selectinload(Upload.posts).lazyload(Post.illust_urls), selectinload(Upload.errors))
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


def create():
    force_download = request.values.get('force', type=EvalBoolString)
    dataparams = GetDataParams(request, 'upload')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckCreateParams(createparams)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    if not force_download:
        upload = GetExistingUpload(createparams)
        if upload is not None:
            retdata['item'] = upload.to_json()
            return SetError(retdata, "Upload already exists: upload #%d" % upload.id)
    if createparams['request_url']:
        source = BASE_SOURCE.GetPostSource(createparams['request_url'])
        if source is None:
            return SetError(retdata, "Upload source currently not handled for request url: %s" % createparams['request_url'])
        createparams['image_urls'] = [url for url in createparams['image_urls'] if source.IsImageUrl(url)]
    upload = CreateUploadFromParameters(createparams)
    retdata['item'] = upload.to_json()
    try:
        requests.get('http://127.0.0.1:4000/check_uploads', timeout=2)
    except Exception as e:
        print("Unable to contact worker:", e)
    return retdata


#   Routes


@bp.route('/uploads/<int:id>.json')
def show_json(id):
    return ShowJson(Upload, id)


@bp.route('/uploads/<int:id>')
def show_html(id):
    upload = GetOrAbort(Upload, id)
    return render_template("uploads/show.html", upload=upload)


@bp.route('/uploads.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/uploads', methods=['GET'])
def index_html():
    q = index()
    uploads = Paginate(q, request)
    return render_template("uploads/index.html", uploads=uploads, upload=Upload())


@bp.route('/uploads/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    illust_url = None
    form = GetUploadForm(**request.args)
    if form.illust_url_id.data is not None:
        illust_url = IllustUrl.find(form.illust_url_id.data)
        if illust_url is None:
            flash("Illust URL #%d does not exist." % form.illust_url_id.data, 'error')
            form.illust_url_id.data = None
        elif illust_url.post is not None:
            flash("Illust URL #%d already uploaded on post #%d." % (illust_url.id, illust_url.post.id), 'error')
            form.illust_url_id.data = None
            illust_url = None
        else:
            HideInput(form, 'illust_url_id', illust_url.id)
            HideInput(form, 'request_url')
            HideInput(form, 'image_url_string')
    return render_template("uploads/new.html", form=form, upload=Upload(), illust_url=illust_url)


@bp.route('/uploads', methods=['POST'])
def create_html():
    if GetMethodRedirect(request):
        return index_html()
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('upload.new_html', **results['data']))
    return redirect(url_for('upload.show_html', id=results['item']['id']))


@bp.route('/uploads.json', methods=['POST'])
def create_json():
    if GetMethodRedirect(request):
        return index_json()
    return create()
