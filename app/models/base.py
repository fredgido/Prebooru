# APP/MODELS/BASE.PY

# ##PYTHON IMPORTS
import datetime
from typing import List, _GenericAlias
from flask import url_for

# ##LOCAL IMPORTS
from .. import DB


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


def PolymorphicAccessorFactory(collection_type, proxy):
    def getter(obj):
        if not hasattr(obj, proxy.value_attr):
            return
        return getattr(obj, proxy.value_attr)

    def setter(obj, value):
        if not hasattr(obj, proxy.value_attr):
            return
        setattr(obj, proxy.value_attr, value)

    return getter, setter


# Classes

class JsonModel(DB.Model):
    __abstract__ = True

    @classmethod
    def find(cls, id):
        return cls.query.filter_by(id=id).first()

    @property
    def shortlink(self):
        return "%s #%d" % (self.__table__.name, self.id)

    @property
    def show_url(self):
        return url_for(self.__table__.name + ".show_html", id=self.id)

    @property
    def index_url(self):
        return url_for(self.__table__.name + ".index_html")

    @property
    def create_url(self):
        return url_for(self.__table__.name + ".create_html")

    @property
    def update_url(self):
        return url_for(self.__table__.name + ".update_html", id=self.id)

    @property
    def delete_url(self):
        return url_for(self.__table__.name + ".delete_html", id=self.id)

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
