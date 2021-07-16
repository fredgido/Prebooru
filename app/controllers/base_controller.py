# APP\CONTROLLERS\BASE_CONTROLLER.PY

# ## PYTHON IMPORTS
import re
import urllib
from functools import reduce
from flask import jsonify, render_template, abort, url_for
from sqlalchemy.sql.expression import case
from wtforms import Form
from flask_wtf import FlaskForm
from wtforms.meta import DefaultMeta
from wtforms.widgets import HiddenInput

# ## LOCAL IMPORTS
from ..logical.searchable import AllAttributeFilters


# ## GLOBAL VARIABLES

# #### Classes


class BindNameMeta(DefaultMeta):
    def bind_field(self, form, unbound_field, options):
        if 'custom_name' in unbound_field.kwargs:
            options['name'] = unbound_field.kwargs.pop('custom_name')
        return unbound_field.bind(form=form, **options)


class CustomNameForm(Form):
    Meta = BindNameMeta


# ## FUNCTIONS


# #### Route helpers


def ReferrerCheck(endpoint, request):
    return urllib.parse.urlparse(request.referrer).path == url_for(endpoint)


def PutMethodCheck(request):
    if request.method == 'POST' and request.values.get('_method', default='').upper() != 'PUT':
        abort(405)


def DeleteMethodCheck(request):
    if request.method == 'POST' and request.values.get('_method', default='').upper() != 'DELETE':
        abort(405)


def GetMethodRedirect(request):
    return request.values.get('_method', default='').upper() == 'GET'


def PutMethodRedirect(request):
    return request.values.get('_method', default='').upper() == 'PUT'


def DeleteMethodRedirect(request):
    return request.values.get('_method', default='').upper() == 'DELETE'


def ShowJson(model, id):
    item = model.query.filter_by(id=id).first()
    return item.to_json() if item is not None else {}


def IndexJson(query, request):
    return jsonify([x.to_json() for x in Paginate(query, request).items])


# #### Query helpers


def SearchFilter(query, search):
    entity = _QueryModel(query)
    return AllAttributeFilters(query, entity, search)


def DefaultOrder(query, search):
    entity = query.column_descriptions[0]['entity']
    if 'order' in search:
        if search['order'] == 'custom':
            ids = [int(id) for id in search['id'].split(',') if id.isdigit()]
            if len(ids) > 1:
                return query.order_by(_CustomOrder(ids, entity))
        elif search['order'] == 'id_asc':
            return query.order_by(entity.id.asc())
    return query.order_by(entity.id.desc())


def Paginate(query, request):
    return query.paginate(page=GetPage(request), per_page=GetLimit(request))


# #### ID helpers


def GetOrAbort(model, id):
    item = model.find(id)
    if item is None:
        abort(404, "%s not found." % model.__name__)
    return item


def GetOrError(model, id):
    item = model.find(id)
    if item is None:
        return {'error': True, 'message': "%s not found." % model.__name__}
    return item


# #### Form helpers


def HideInput(form, attr, value=None):
    field = getattr(form, attr)
    if value is not None:
        field.data = value
    field.widget = HiddenInput()
    field._value = lambda: field.data


# #### Param helpers


def GetPage(request):
    return int(request.args['page']) if 'page' in request.args else 1


def GetLimit(request):
    return int(request.args['limit']) if 'limit' in request.args else 20


def ProcessRequestValues(values_dict):
    params = {}
    for key in values_dict:
        match = re.match(r'^([^[]+)(.*)', key)
        if not match:
            continue
        primary_key, sub_groups = match.groups()
        is_subhash = _AssignParams(values_dict, key, params, primary_key, sub_groups)
        if is_subhash is None:
            continue
        if not is_subhash:
            continue
        is_valid = _ProcessRequestValuesRecurse(values_dict, key, sub_groups, params[primary_key])
        if not is_valid:
            del params[primary_key]
    return params


def GetParamsValue(params, key, is_hash=False):
    default = {} if is_hash else None
    value = params.get(key, default)
    if is_hash and type(value) is not dict:
        value = default
    return value


def GetDataParams(request, key):
    params = ProcessRequestValues(request.values)
    return GetParamsValue(params, key, True)


def SetError(retdata, message):
    retdata['error'] = True
    retdata['message'] = message
    return retdata


def ParseType(params, key, parser):
    try:
        return parser(params[key])
    except Exception as e:
        return None


def ParseStringList(params, key, separator):
    return [item.strip() for item in re.split(separator, params[key]) if item.strip() != ""]


def CheckParamRequirements(params, requirements):
    return reduce(lambda acc, x: acc + (["%s not present or invalid." % x] if params[x] is None else []), requirements, [])


def IntOrBlank(data):
    try:
        return int(data)
    except Exception:
        return ""


def NullifyBlanks(data):
    def _Check(val):
        return type(val) is str and val.strip() == ""
    return {k:(v if not _Check(v) else None) for (k,v) in data.items()}


def SetDefault(indict, key, default):
    indict[key] = indict[key] if key in indict else default


# #### Update helpers


def UpdateColumnAttributes(item, attrs, dataparams, updateparams):
    is_dirty = False
    for attr in attrs:
        if attr in dataparams and getattr(item, attr) != updateparams[attr]:
            print("Setting basic attr:", attr, updateparams[attr])
            setattr(item, attr, updateparams[attr])
            is_dirty = True
    return is_dirty


def UpdateRelationshipCollections(item, relationships, dataparams, updateparams):
    """For simple collection relationships with scalar values"""
    is_dirty = False
    for attr, subattr, model in relationships:
        if attr not in dataparams:
            continue
        collection = getattr(item, attr)
        current_values = [getattr(subitem, subattr) for subitem in collection]
        add_values = set(updateparams[attr]).difference(current_values)
        for value in add_values:
            print("Adding collection item:", attr, value)
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
            collection.append(add_item)
            is_dirty = True
        remove_values = set(current_values).difference(updateparams[attr])
        for value in remove_values:
            print("Removing collection item:", attr, value)
            remove_item = next(filter(lambda x: getattr(x, subattr) == value, collection))
            collection.remove(remove_item)
            is_dirty = True
    return is_dirty


# #### Private functions


def _CustomOrder(ids, entity):
    return case(
        {id: index for index, id in enumerate(ids)},
        value=entity.id,
    )


def _QueryModel(query):
    return query.column_descriptions[0]['entity']


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
    return None


def _ProcessRequestValuesRecurse(values_dict, key, sub_keys, params):
    secondary_key, sub_groups = re.match(r'^\[([^[]+)\](.*)', sub_keys).groups()
    result = _AssignParams(values_dict, key, params, secondary_key, sub_groups)
    if result is None:
        return False
    if result:
        return _ProcessRequestValuesRecurse(values_dict, key, sub_groups, params[secondary_key])
    return True
