# APP\CONTROLLERS\POOL_ELEMENTS_CONTROLLER.PY

# ## PYTHON IMPORTS
import time
from flask import Blueprint, request, render_template, url_for, flash, redirect
from wtforms import IntegerField
from wtforms.validators import DataRequired
from sqlalchemy import and_, or_
from sqlalchemy.orm import selectinload


# ## LOCAL IMPORTS
from ..similarity import SimilarityPool, SimilarityPoolElement
from ..database import local as DBLOCAL
from ..logical.utility import GetCurrentTime
from .base_controller import GetDataParams, CustomNameForm, ParseType, ReferrerCheck, DeleteMethodCheck, GetOrAbort, ParseListType


# ## GLOBAL VARIABLES

bp = Blueprint("similarity_pool_element", __name__)


# ## FUNCTIONS

def batch_delete():
    dataparams = GetDataParams(request, 'similarity_pool_element')
    dataparams['id'] = ParseListType(dataparams, 'id', int)
    print("Params:", dataparams)
    if dataparams['id'] is None or len(dataparams['id']) == 0:
        return
    start_time = time.time()
    pool_elements_1 = SimilarityPoolElement.query.options(selectinload(SimilarityPoolElement.pool)).filter(SimilarityPoolElement.id.in_(dataparams['id'])).all()
    print("#1", time.time() - start_time, pool_elements_1)
    if len(pool_elements_1) == 0:
        return
    post_ids_1 = [element.post_id for element in pool_elements_1]
    start_time = time.time()
    pools = SimilarityPool.query.filter(SimilarityPool.post_id.in_(post_ids_1)).all()
    print("#P", time.time() - start_time, pools)
    start_time = time.time()
    filters = []
    for element in pool_elements_1:
        pool = next(filter(lambda x: x.post_id == element.post_id, pools))
        filters.append(and_(SimilarityPoolElement.pool_id == pool.id, SimilarityPoolElement.post_id == element.pool.post_id))
    print("#F", time.time() - start_time)
    start_time = time.time()
    pool_elements_2 = SimilarityPoolElement.query.filter(or_(*filters)).all()
    print("#2", time.time() - start_time, pool_elements_2)
    start_time = time.time()
    """
    for element in (pool_elements_1 + pool_elements_2):
        DBLOCAL.RemoveData(element)
    """
    element_ids = [element.id for element in (pool_elements_1 + pool_elements_2)]
    SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(element_ids)).delete()
    DBLOCAL.SaveData()
    print("END", time.time() - start_time)

# #### Route functions

@bp.route('/similarity_pool_elements/<int:id>', methods=['POST', 'DELETE'])
def delete_html(id):
    DeleteMethodCheck(request)
    pool_element_1 = GetOrAbort(SimilarityPoolElement, id)
    post_id_2 = pool_element_1.pool.post_id
    # All posts should have a similarity pool, so no need to check for none
    pool_2 = SimilarityPool.query.filter_by(post_id=pool_element_1.post_id).first()
    pool_element_2 = SimilarityPoolElement.query.filter_by(post_id=post_id_2, pool_id=pool_2.id).first()
    print(pool_element_1, pool_element_2)
    DBLOCAL.RemoveData(pool_element_1)
    if pool_element_2 is not None:
        DBLOCAL.RemoveData(pool_element_2)
    DBLOCAL.SaveData()
    flash("Removed from post.")
    return redirect(request.referrer)


@bp.route('/similarity_pool_elements', methods=['POST', 'DELETE'])
def batch_delete_html():
    DeleteMethodCheck(request)
    batch_delete()
    return redirect(request.referrer)
