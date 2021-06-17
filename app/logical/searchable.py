import re
from sqlalchemy import and_, or_, not_
import sqlalchemy.sql.sqltypes as sqltypes
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy import func as sqlfuncs

from .utility import IsTruthy, IsFalsey, ProcessUTCTimestring

def IsRelationship(model, columnname):
    return type(getattr(model, columnname).property) is RelationshipProperty

def RelationshipModel(model, columnname):
    return getattr(model, columnname).property.mapper.class_

def IsCollection(model, columnname):
    return getattr(model, columnname).property.uselist

def IsColumn(model, columnname):
    return columnname in model.__table__.c.keys()

def SQLEscape(value):
    retvalue = value.replace('%', '\x01%')
    retvalue = retvalue.replace('_', '\x01_')
    retvalue = re.sub(r'(?<!\\)\*', '%', retvalue)
    retvalue = retvalue.replace('\*', '*')
    return retvalue

def ColumnType(model, columnname):
    switcher = {
        sqltypes.Integer: 'INTEGER',
        sqltypes.Float: 'FLOAT',
        sqltypes.DateTime: 'DATETIME',
        sqltypes.Boolean: 'BOOLEAN',
        sqltypes.String: 'STRING',
        sqltypes.Text: 'TEXT',
        sqltypes.Unicode: 'STRING',
        sqltypes.UnicodeText: 'TEXT',
    }
    column_type = type(getattr(model.__table__.c, columnname).type)
    try:
        return switcher[column_type]
    except Exception:
        raise Exception("%s - column of unexpected type: %s" % (columnname, str(column_type)))

def AllAtributeFilters(model, params, *columnnames):
    query_filters = ()
    for columnname in columnnames:
        query_filters += AttributeFilters(model, columnname, params)
    return query_filters

def AttributeFilters(model, columnname, params):
    if IsColumn(model, columnname):
        return BasicAttributeFilters(model, columnname, params)
    if IsRelationship(model, columnname):
        return ()
    raise Exception("%s is not a column or relationship" % columnname);

def BasicAttributeFilters(model, columnname, params):
    switcher = {
        'INTEGER': NumericFilters,
        'DATETIME': NumericFilters,
        'FLOAT': NumericFilters,
        'BOOLEAN': BooleanFilters,
        'STRING': TextFilters,
        'TEXT': TextFilters,
    }
    type = ColumnType(model, columnname)
    return switcher[type](model, columnname, params)

def NumericFilters(model, columnname, params):
    type = ColumnType(model, columnname)
    parser = lambda x: ParseCast(x, type)
    filters = ()
    if columnname in params:
        filters += (NumericMatching(model, columnname, params[columnname]),)
    if (columnname + '_not') in params:
        filters += (not_(NumericMatching(model, columnname, params[columnname + '_not'])),)
    if (columnname + '_eq') in params:
        filters += (getattr(model, columnname) == parser(params[columnname + '_eq']),)
    if (columnname + '_ne') in params:
        filters += (getattr(model, columnname) != parser(params[columnname + '_ne']),)
    if (columnname + '_gt') in params:
        filters += (getattr(model, columnname) > parser(params[columnname + '_gt']),)
    if (columnname + '_ge') in params:
        filters += (getattr(model, columnname) >= parser(params[columnname + '_ge']),)
    if (columnname + '_lt') in params:
        filters += (getattr(model, columnname) < parser(params[columnname + '_lt']),)
    if (columnname + '_le') in params:
        filters += (getattr(model, columnname) <= parser(params[columnname + '_le']),)
    return filters

def NumericMatching(model, columnname, value):
    type = ColumnType(model, columnname)
    parser = lambda x: ParseCast(x, type)
    match = re.match(r'(.+?)\.\.(.+)', value)
    if match:
        return getattr(model, columnname).between(*map(parser, re.match('(.+?)\.\.(.+)', value).groups()))
    match = re.match(r'<=(.+)', value) or re.match(r'\.\.(.+)', value)
    if match:
        return getattr(model, columnname) <= parser(match.group(1))
    match = re.match(r'<(.+)', value)
    if match:
        return getattr(model, columnname) < parser(match.group(1))
    match = re.match(r'>=(.+)', value) or re.match(r'(.+)\.\.$', value)
    if match:
        return getattr(model, columnname) >= parser(match.group(1))
    match = re.match(r'>(.+)', value)
    if match:
        return getattr(model, columnname) > parser(match.group(1))
    if re.match(r'[ ,]', value):
        return getattr(model, columnname).in_(map(parser, re.split(r'[ ,]', value)))
    if value == 'any':
        return getattr(model, columnname) != None
    if value == 'none':
        return getattr(model, columnname) == None
    #Check searchable concern for other checks/tests other than integer
    return getattr(model, columnname) == parser(value)

def BooleanFilters(model, columnname, params):
    if columnname in params:
        return BooleanMatching(model, columnname, params[columnname])
    return ()

def BooleanMatching(model, columnname, value):
    if IsTruthy(value):
        return (getattr(model, columnname) == True,)
    if IsFalsey(value):
        return (getattr(model, columnname) == False,)
    raise Exception("%s - value must be truthy or falsey" % columnname)

def TextFilters(model, columnname, params):
    filters = ()
    if columnname in params:
        filters += (getattr(model, columnname) == params[columnname],)
    if (columnname + '_eq') in params:
        filters += (getattr(model, columnname) == params[columnname + '_eq'],)
    if (columnname + '_ne') in params:
        filters += (getattr(model, columnname) != params[columnname + '_ne'],)
    if (columnname + '_like') in params:
        filters += (getattr(model, columnname).like(SQLEscape(params[columnname + '_like']), escape='\x01'),)
    if (columnname + '_ilike') in params:
        filters += (getattr(model, columnname).ilike(SQLEscape(params[columnname + '_ilike']), escape='\x01'),)
    if (columnname + '_not_like') in params:
        filters += (not_(getattr(model, columnname).like(SQLEscape(params[columnname + '_not_like']), escape='\x01')),)
    if (columnname + '_not_ilike') in params:
        filters += (not_(getattr(model, columnname).ilike(SQLEscape(params[columnname + '_not_ilike']), escape='\x01')),)
    if (columnname + '_regex') in params:
        filters += (getattr(model, columnname).regexp_match(params[columnname + '_regex']),)
    if (columnname + '_not_regex') in params:
        filters += (not_(getattr(model, columnname).regexp_match(params[columnname + '_not_regex'])),)
    if (columnname + '_exists') in params:
        if IsTruthy(params[columnname + '_exists']):
            filters += (getattr(model, columnname) != None,)
        elif IsFalsey(params[columnname + '_exists']):
            filters += (getattr(model, columnname) == None,)
        else:
            raise Exception("%s - value must be truthy or falsey" % (columnname + '_exists'))
    if (columnname + '_array') in params:
        filters += (getattr(model, columnname).in_(params[columnname + '_array']),)
    if (columnname + '_comma') in params:
        filters += (getattr(model, columnname).in_(params[columnname + '_comma'].split(',')),)
    if (columnname + '_space') in params:
        filters += (getattr(model, columnname).in_(params[columnname + '_comma'].split(' ')),)
    if (columnname + '_lower_array') in params:
        filters += (sqlfuncs.lower(getattr(model, columnname)).in_(params[columnname + '_array']),)
    if (columnname + '_lower_comma') in params:
        filters += (sqlfuncs.lower(getattr(model, columnname)).in_(params[columnname + '_comma'].split(',')),)
    if (columnname + '_lower_space') in params:
        filters += (sqlfuncs.lower(getattr(model, columnname)).in_(params[columnname + '_comma'].split(' ')),)
    return filters

def ParseCast(value, type):
    if type == 'INTEGER':
        return int(value)
    if type == 'DATETIME':
        return ProcessUTCTimestring(value)
    if type == 'FLOAT':
        return float(value)
    return value

"""
Passing True in as one of the arguments is equivalent to ALL in rails
Passing False in as one of the arguments is equivalent to NONE in rails
"""

"""
app.models.Artist.query.filter(app.models.Artist.id.between(1,6)).all()
"""
