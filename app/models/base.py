# APP/MODELS/BASE.PY

# ##PYTHON IMPORTS
import datetime
from typing import List, _GenericAlias

# ##LOCAL IMPORTS
from .. import db


# ##FUNCTIONS

# Auxiliary functions

def DateTimeOrNull(value):
    return value if value is None else datetime.datetime.isoformat(value)


def IntOrNone(data):
    return data if data is None else int(data)


def StrOrNone(data):
    return data if data is None else str(data)


def RemoveKeys(data, keylist):
    return {k: data[k] for k in data if k not in keylist}

# Classes


class JsonModel(db.Model):
    __abstract__ = True

    def to_json(self):
        fields = self.__dataclass_fields__
        data = {}
        for key in fields:
            value = getattr(self, key)
            type_func = fields[key].type
            if type_func is None:
                data[key] = None
            elif 'to_json' in dir(type_func):
                data[key] = value.to_json()
            elif type_func == List:
                data[key] = [t.to_json() for t in value]
            elif isinstance(type_func, _GenericAlias):
                subtype_func = type_func.__args__[0]
                data[key] = [subtype_func(t.to_json()) for t in value]
            else:
                data[key] = type_func(value)
        return data