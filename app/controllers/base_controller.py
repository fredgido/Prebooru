# APP\CONTROLLERS\BASE_CONTROLLER.PY

# ## PYTHON IMPORTS
import re
from flask import jsonify, render_template
from sqlalchemy.sql.expression import case
from wtforms import TextAreaField, IntegerField, Form
from wtforms.meta import DefaultMeta

# ## LOCAL IMPORTS
from ..logical.searchable import AllAttributeFilters 

# ## GLOBAL VARIABLES

class BindNameMeta(DefaultMeta):
    def bind_field(self, form, unbound_field, options):
        if 'custom_name' in unbound_field.kwargs:
            options['name'] = unbound_field.kwargs.pop('custom_name')
        return unbound_field.bind(form=form, **options)

class CustomNameForm(Form):
    Meta = BindNameMeta


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

def GetParamsValue(params, key, is_hash=False):
    default = {} if is_hash else None
    value = params.get(key, default)
    if is_hash and type(value) is not dict:
        value = default
    return value

def ProcessRequestValues(values_dict):
    params = {}
    for key in values_dict:
        match = re.match(r'^([^[]+)(.*)', key)
        if not match:
            print("ProcessParams - no initial key.")
            continue
        primary_key, sub_groups = match.groups()
        is_subhash = _AssignParams(values_dict, key, params, primary_key, sub_groups)
        if is_subhash is None:
            continue
        if not is_subhash:
            continue
        is_valid = _ProcessParamsRecurse(values_dict, key, sub_groups, params[primary_key])
        if not is_valid:
            del params[primary_key]
    return params

def _ProcessParamsRecurse(values_dict, key, sub_keys, params):
    #print("ProcessParamsRecurse:", values_dict, key, sub_keys, params)
    secondary_key, sub_groups = re.match(r'^\[([^[]+)\](.*)', sub_keys).groups()
    result = _AssignParams(values_dict, key, params, secondary_key, sub_groups)
    if result is None:
        return False
    if result:
        return _ProcessParamsRecurse(values_dict, key, sub_groups, params[secondary_key])
    return True

def _AssignParams(values_dict, key, params, primary_key, sub_groups):
    if sub_groups == '':
        params[primary_key] = values_dict.get(key)
        return False
    elif sub_groups == '[]':
        params[primary_key] = values_dict.getlist(key)
        return False
    elif re.match(r'^\[.*\]$', sub_groups):
        params[primary_key] = params[primary_key] if primary_key in params else {}
        params[primary_key] = params[primary_key] if type(params[primary_key]) is dict else {}
        return True
    print("ProcessParams - incorrect sub groups.", primary_key, sub_groups)
    return None


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

def SearchFilter(query, search):
    entity = QueryModel(query)
    return AllAttributeFilters(query, entity, search)

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
