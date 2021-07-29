# APP\CONTROLLERS\SIMILARITY_CONTROLLER.PY

# ## PYTHON IMPORTS
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, request, render_template, abort, Markup, jsonify, redirect

# ## LOCAL IMPORTS
from .. import PREBOORU
from ..logical.file import PutGetRaw
from ..models import Post
from ..config import DANBOORU_USERNAME, DANBOORU_APIKEY

bp = Blueprint("similarity", __name__)

@bp.route('/similarity/check', methods=['GET'])
def check():
    resp = requests.get('http://127.0.0.1:3000/check_similarity.json', params=request.args)
    if resp.status_code != 200:
        abort(503, "Unable to contact similarity server: %d - %s" % (resp.status_code, resp.reason))
    data = resp.json()
    if data['error']:
        abort(504, data['message'])
    for similarity_result in data['similar_results']:
        post_ids = [result['post_id'] for result in similarity_result['post_results']]
        posts = Post.query.filter(Post.id.in_(post_ids)).all()
        for result in similarity_result['post_results']:
            post = next(filter(lambda x: x.id == result['post_id'], posts), None)
            result['post'] = post
    return render_template("similarity/check.html", similar_results=data['similar_results'])
