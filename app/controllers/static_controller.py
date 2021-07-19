# APP\CONTROLLERS\STATIC_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, Markup, jsonify, redirect

# ## LOCAL IMPORTS
from ..logical.file import PutGetRaw
from ..sources import base as BASE_SOURCE
from ..models import Post
from .base_controller import GetDataParams
from ..config import DANBOORU_USERNAME, DANBOORU_APIKEY

bp = Blueprint("static", __name__)

@bp.route('/static/site_map', methods=['GET'])
def site_map_html():
    return render_template("static/site_map.html")
