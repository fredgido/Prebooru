# APP\CONTROLLERS\POOLS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, url_for, flash, redirect
from sqlalchemy.orm import lazyload, selectinload
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from ..similarity import SimilarityPool
from ..models import Pool, Post, Illust, Notation, IllustUrl, PoolPost, PoolIllust, PoolNotation
from ..database import local as DBLOCAL
from ..logical.utility import GetCurrentTime
from ..logical.searchable import NumericMatching
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate,\
    DefaultOrder, GetDataParams, CustomNameForm, GetPage, GetLimit, ParseType, GetOrAbort


# ## GLOBAL VARIABLES

bp = Blueprint("similarity_pool", __name__)


# ## FUNCTIONS

# #### Helper functions

# #### Route functions

@bp.route('/similarity_pools/<int:id>', methods=['GET'])
def show_html(id):
    similarity_pool = GetOrAbort(SimilarityPool, id)
    post = Post.find(similarity_pool.post_id)
    elements = similarity_pool.element_paginate(page=GetPage(request), per_page=GetLimit(request))
    return render_template("similarity_pools/show.html", similarity_pool=similarity_pool, post=post, elements=elements)
