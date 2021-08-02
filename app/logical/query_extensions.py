# APP/LOGICAL/UNSHORTENLINK.PY

# ##PYTHON IMPORTS
import sqlalchemy.orm
from sqlalchemy import func


# ##GLOBAL VARIABLES

INIT = False


# ##FUNCTIONS

# #### Initialization functions

def Initialize():
    """This can only be set after the models have been initialized"""
    global INIT
    if not INIT:
        sqlalchemy.orm.Query._has_entity = _has_entity
        sqlalchemy.orm.Query.unique_join = unique_join
        sqlalchemy.orm.Query.get_count = get_count
        INIT = True


# #### Extension functions

def unique_join(self, model, *args, **kwargs):
    if not self._has_entity(model):
        self = self.join(model, *args, **kwargs)
    return self


def get_count(self):
    return self.with_entities(func.count()).scalar()


# #### Private functions

def _has_entity(self, model):
    current_joined_tables = [t[0] for t in self._legacy_setup_joins]
    return model.__table__ in current_joined_tables
