# APP\CONTROLLERS\BASE.PY

# ## PYTHON IMPORTS
import re
from flask import jsonify


# ## FUNCTIONS


def ShowJson(model, id):
    item = model.query.filter_by(id=id).first()
    return item.to_json() if item is not None else {}


def IndexJson(query, request):
    items = query.paginate(page=GetPage(request), per_page=GetLimit(request)).items
    return jsonify([x.to_json() for x in items])


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


def IdFilter(query, search):
    if 'id' in search:
        ids = [int(id) for id in search['id'].split(',') if id.isdigit()]
        if len(ids) == 1:
            query = query.filter_by(id=ids[0])
        else:
            entity = query.column_descriptions[0]['entity']
            query = query.filter(entity.id.in_(ids))
    return query
