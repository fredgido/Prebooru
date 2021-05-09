import re
from sqlalchemy import and_, or_, not_
from sqlalchemy.sql.sqltypes import Integer, Datetime
from sqlalchemy.orm.relationships import RelationshipProperty

from .utility import ProcessTimestamp

def IsRelationship(model, columnname):
    return type(getattr(model, columnname).property) is RelationshipProperty

def RelationshipModel(model, columnname):
    return getattr(model, columnname).property.mapper.class_

def IsCollection(model, columnname):
    return getattr(model, columnname).property.uselist

def IsColumn(model, columnname):
    return columnname in model.__table__.c.keys()

def ColumnType(model, columnname):
    return str(getattr(model.__table__.c, columnname).type)

def AttributeFilter(mode, columnname, params):
    if IsColumn(model, columnname):
        return BasicAttributeFilter(model, columnname, params)
    return True

def BasicAttributeFilter(model, columnname, params):
    switcher = {
        'INTEGER': CreateIntegerFilter,
    }
    type = ColumnType(model, columnname):
    if type not in switcher:
        return True
    return switcher[type](model, columnname, value)

def NumericFilters(model, columnname, params):
    filters = (True,)
    if columnname in params:
        filters += (NumericMatching(model, columnname, params[columnname]),)
    if (columnname + '_not') in params:
        filters += not_(NumericMatching(model, columnname, params[columnname + '_not']),)
    if (columnname + '_eq') in params:
        filters += (getattr(model, columnname) == params[columnname + '_eq'],)
    if (columnname + '_ne') in params:
        filters += (getattr(model, columnname) != params[columnname + '_ne'],)
    if (columnname + '_gt') in params:
        filters += (getattr(model, columnname) > params[columnname + '_gt'],)
    if (columnname + '_ge') in params:
        filters += (getattr(model, columnname) >= params[columnname + '_ge'],)
    if (columnname + '_lt') in params:
        filters += (getattr(model, columnname) < params[columnname + '_lt'],)
    if (columnname + '_le') in params:
        filters += (getattr(model, columnname) <= params[columnname + '_le'],)
    return filters

def NumericMatching(model, columnname, value):
    type = ColumnType(model, columnname)
    parser = lambda x: ParseCast(x, type)
    match = re.match(r'(.+?)\.\.(.+)', value)
    if match:
        return getattr(model, columnname).between(*map(parser, re.match('(.+?)\.\.(.+)', '12..13').groups()))
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
    return getattr(model, columnname) == value

def ParseCast(value, type):
    if type == 'INTEGER':
        return int(value)
    if type == 'DATETIME':
        return ProcessUTCTimestring(value)
    return value

"""
Passing True in as one of the arguments is equivalent to ALL in rails
Passing False in as one of the arguments is equivalent to NONE in rails
"""

"""
app.models.Artist.query.filter(app.models.Artist.id.between(1,6)).all()
"""
