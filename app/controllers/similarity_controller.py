# APP\CONTROLLERS\SIMILARITY_CONTROLLER.PY

# ## PYTHON IMPORTS
import imagehash
import requests
from types import SimpleNamespace

from PIL import Image
from flask import Blueprint, request, render_template, abort
from wtforms import TextAreaField, BooleanField, FloatField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from ..database.post_db import GetPostsByID
from .base_controller import ProcessRequestValues, CustomNameForm, ParseArrayParameter, ParseBoolParameter, ParseType, \
    BuildUrlArgs, SetError

# ## GLOBAL VARIABLES
from ..logical.similarity import CreateNewMedia, \
    CheckSimilarMatchScores, generate_posts_similarity
from ..models import Post, SimilarityData, MediaFile
from ..models.similarity_data import HASH_SIZE
from ..sources.base_source import GetImageSource, NoSource

bp = Blueprint("similarity", __name__)


# #### Forms

def GetSimilarityForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class SimilarityForm(CustomNameForm):
        urls_string = TextAreaField('URLs', id='similarity-urls', custom_name='urls_string', description="Separated by carriage returns.", validators=[DataRequired()])
        score = FloatField('Score', id='similarity-score', description="Lowest score of results to return. Default is 90.0.")
        use_original = BooleanField('Use Original', id='similarity-use-original', description="Uses the original image URL instead of the small version.")
    return SimilarityForm(**kwargs)


# ## FUNCTIONS

# #### Route functions

@bp.route('/similarity/check', methods=['GET'])
def check_html():
    params = ProcessRequestValues(request.args)
    params['urls'] = ParseArrayParameter(params, 'urls', 'urls_string', r'\r?\n')
    params['score'] = ParseType(params, 'score', float)
    params['use_original'] = ParseBoolParameter(params, 'use_original')
    if params['urls'] is None or len(params['urls']) is None:
        return render_template("similarity/check.html", similar_results=None, form=GetSimilarityForm(**params))
    try:
        resp = requests.get('http://127.0.0.1:3000/check_similarity.json', params=BuildUrlArgs(params, ['urls', 'score', 'use_original']))
    except requests.exceptions.ReadTimeout:
        abort(502, "Unable to contact similarity server.")
    if resp.status_code != 200:
        abort(503, "Error with similarity server: %d - %s" % (resp.status_code, resp.reason))
    data = resp.json()
    if data['error']:
        abort(504, data['message'])
    similar_results = []
    for json_result in data['similar_results']:
        similarity_result = SimpleNamespace(**json_result)
        similarity_result.post_results = [SimpleNamespace(**post_result) for post_result in similarity_result.post_results]
        post_ids = [post_result.post_id for post_result in similarity_result.post_results]
        posts = GetPostsByID(post_ids)
        for post_result in similarity_result.post_results:
            post_result.post = next(filter(lambda x: x.id == post_result.post_id, posts), None)
        similar_results.append(similarity_result)
    params['url_string'] = '\r\n'.join(params['urls'])
    return render_template("similarity/check.html", similar_results=similar_results, form=GetSimilarityForm(**params))


@bp.route('/similarity/check_similarity.json', methods=['GET'])
def check_similarity():
    request_urls = request.args.getlist('urls[]')
    request_score = request.args.get('score', type=float, default=90.0)
    use_original = request.args.get('use_original', type=bool, default=False)
    include_posts = request.args.get('include_posts', type=bool, default=False)
    retdata = {'error': False}
    if request_urls is None:
        return SetError(retdata, "Must include url.")
    similar_results = []
    for image_url in request_urls:
        source = GetImageSource(image_url) or NoSource()
        download_url = source.SmallImageUrl(image_url) if source is not None and not use_original else image_url
        media = MediaFile.query.filter_by(media_url=download_url).first()
        if media is None:
            media, image = CreateNewMedia(download_url, source)
            if type(image) is str:
                return SetError(retdata, image)
        else:
            image = Image.open(media.file_path)
        image = image.copy().convert("RGB")
        image_hash = str(imagehash.whash(image, hash_size=HASH_SIZE))
        ratio = round(image.width / image.height, 4)
        smatches = SimilarityData.query.filter(SimilarityData.ratio_clause(ratio), SimilarityData.cross_similarity_clause2(image_hash)).all()
        score_results = CheckSimilarMatchScores(smatches, image_hash, request_score)
        all_post_ids = set(result['post_id'] for result in score_results)
        final_results = []
        for post_id in all_post_ids:
            post_results = [result for result in score_results if result['post_id'] == post_id]
            if len(post_results) > 1:
                post_results = sorted(post_results, key=lambda x: x['score'], reverse=True)
            final_results.append(post_results[0])
        final_results = sorted(final_results, key=lambda x: x['score'], reverse=True)
        if include_posts:
            post_ids = [result['post_id'] for result in final_results]
            posts = Post.query.filter(Post.id.in_(post_ids)).all()
            for result in final_results:
                post = next(filter(lambda x: x.id == result['post_id'], posts), None)
                result['post'] = post.to_json() if post is not None else post
        normalized_url = source.NormalizedImageUrl(image_url) if not use_original else image_url
        similar_results.append({'image_url': normalized_url, 'post_results': final_results, 'cache': media.file_url})
    retdata['similar_results'] = similar_results
    return retdata


@bp.route('/similarity/generate_similarity.json', methods=['POST'])
def generate_similarity():
    data = request.get_json()
    post_ids = data.get('post_ids')
    if not post_ids:
        return {'error': True, 'message': "Must include post_ids."}
    generate_posts_similarity(data)
    return {'error': False}


