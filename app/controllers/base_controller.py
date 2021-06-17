# APP\CONTROLLERS\BASE.PY

# ## PYTHON IMPORTS
import re
from flask import jsonify, render_template
from sqlalchemy.sql.expression import case

from app.logical.searchable import AllAtributeFilters 

# ## FUNCTIONS

def TemplatePath(model):
    return model.__name__.lower() + 's/'


def ShowJson(model, id):
    item = model.query.filter_by(id=id).first()
    return item.to_json() if item is not None else {}


def ShowHtml(model, id):
    item = model.query.filter_by(id=id).first()
    return render_template
    return item.to_json() if item is not None else {}


def Paginate(query, request):
    return query.paginate(page=GetPage(request), per_page=GetLimit(request))


def IndexJson(query, request):
    return jsonify([x.to_json() for x in Paginate(query, request).items])


def GetPage(request):
    return int(request.args['page']) if 'page' in request.args else 1


def GetLimit(request):
    return int(request.args['limit']) if 'limit' in request.args else 20


def GetSearch(request):
    data = {}
    for arg in request.args:
        match = re.match(r'^search\[([^\]]+)\]', arg)
        if not match:
            continue
        key = match.group(1)
        data[key] = request.args[arg]
    return data


def GetDataParams(request, type):
    data = {}
    for arg in request.values:
        match = re.match(r'^%s\[([^\]]+)\](\[\])?' % type, arg)
        if not match:
            continue
        key = match.group(1)
        if match.group(2) is not None:
            data[key] = request.values.getlist(arg)
        else:
            data[key] = request.values.get(arg)
    return data

def QueryModel(query):
    return query.column_descriptions[0]['entity']

def IdFilter(query, search):
    if 'id' in search:
        ids = [int(id) for id in search['id'].split(',') if id.isdigit()]
        if len(ids) == 1:
            query = query.filter_by(id=ids[0])
        else:
            entity = query.column_descriptions[0]['entity']
            query = query.filter(entity.id.in_(ids))
    return query

def SearchFilter(query, search, *attributes):
    entity = QueryModel(query)
    return query.filter(*AllAtributeFilters(entity, search, *attributes))
    

def CustomOrder(ids, entity):
    return case(
        {id: index for index, id in enumerate(ids)},
        value=entity.id
     )

def DefaultOrder(query, search):
    entity = query.column_descriptions[0]['entity']
    if 'order' in search:
        if search['order'] == 'custom':
            ids = [int(id) for id in search['id'].split(',') if id.isdigit()]
            if len(ids) > 1:
                return query.order_by(CustomOrder(ids, entity))
        elif search['order'] == 'id_asc':
            return query.order_by(entity.id.asc())
    return query.order_by(entity.id.desc())

def PageNavigation(paginate, request):
    current_page = paginate.page
    previous_page = paginate.prev_num
    next_page = paginate.next_num
    last_page = paginate.pages
    left = max(current_page - 4, 2)
    penultimate_page = last_page - 1
    right = min(current_page + 4, penultimate_page)
    pages = [1]
    pages += ['...'] if left != 2 else []
    pages += list(range(left, right))
    pages += ['...'] if right != penultimate_page else []
    pages += [last_page] if last_page != 1 else []
    return render_template("paginator.html", prev_page=previous_page, current_page=current_page, next_page=next_page, pages=pages)
