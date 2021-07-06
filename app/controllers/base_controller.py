# APP\CONTROLLERS\BASE_CONTROLLER.PY

# ## PYTHON IMPORTS
import re
from flask import jsonify, render_template
from sqlalchemy.sql.expression import case
from wtforms import Form
from wtforms.meta import DefaultMeta

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


def ShowJson(model, id):
    item = model.query.filter_by(id=id).first()
    return item.to_json() if item is not None else {}


def ShowHtml(model, id):
    item = model.query.filter_by(id=id).first()
    return render_template
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


def ParseType(params, key, parser):
    try:
        return parser(params[key])
    except Exception as e:
        return None


# #### Model helper


def UpdateColumnAttributes(item, attrs, dataparams, updateparams):
    is_dirty = False
    for attr in attrs:
        if attr in dataparams and getattr(item, attr) != updateparams[attr]:
            print("Setting basic attr:", attr, updateparams[attr])
            setattr(item, attr, updateparams[attr])
            is_dirty = True
    return is_dirty


def UpdateRelationshipCollections(item, rellationships, dataparams, updateparams):
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
