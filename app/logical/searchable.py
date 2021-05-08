from sqlalchemy import and_, or_, not_
from sqlalchemy.sql.sqltypes import Integer, Datetime

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

def NumericFilter(model, columnname, params):
    filters = (True,)
    if columnname in params:
        filters += NumericMatchesFilter(model, columnname, params[columnname]
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
    if (columnname + '_eq') in params:
        filters += (getattr(model, columnname) == params[columnname + '_eq'],)
    if (columnname + '_eq') in params:
        filters += (getattr(model, columnname) == params[columnname + '_eq'],)
    return filters


"""
Passing True in as one of the arguments is equivalent to ALL in rails
Passing False in as one of the arguments is equivalent to NONE in rails
"""

"""
app.models.Artist.query.filter(app.models.Artist.id.between(1,6)).all()
"""
