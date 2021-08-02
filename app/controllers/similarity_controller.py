# APP\CONTROLLERS\SIMILARITY_CONTROLLER.PY

# ## PYTHON IMPORTS
import requests
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
    for similarity_result in data['similar_results']:
        post_ids = [result['post_id'] for result in similarity_result['post_results']]
        posts = GetPostsByID(post_ids)
        for result in similarity_result['post_results']:
            post = next(filter(lambda x: x.id == result['post_id'], posts), None)
            result['post'] = post
    return render_template("similarity/check.html", similar_results=data['similar_results'])
