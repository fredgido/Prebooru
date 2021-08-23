# APP\CONTROLLERS\SIMILARITY_CONTROLLER.PY

# ## PYTHON IMPORTS
import requests
from types import SimpleNamespace
from flask import Blueprint, request, render_template, abort

# ## LOCAL IMPORTS
from ..database.post_db import GetPostsByID


# ## GLOBAL VARIABLES

bp = Blueprint("similarity", __name__)


# ## FUNCTIONS

# #### ROUTE FUNCTIONS

@bp.route('/similarity/check', methods=['GET'])
def check():
    try:
        resp = requests.get('http://127.0.0.1:3000/check_similarity.json', params=request.args)
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
    return render_template("similarity/check.html", similar_results=similar_results)
