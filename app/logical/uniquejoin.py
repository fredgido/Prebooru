import sqlalchemy.orm

INIT = False

def _has_entity(self, model):
    current_joined_tables = [t[0] for t in self._legacy_setup_joins]
    return model.__table__ in current_joined_tables

def unique_join(self, model, *args, **kwargs):
    if not self._has_entity(model):
        self = self.join(model, *args, **kwargs)
    return self

def Initialize():
    global INIT
    if not INIT:
        sqlalchemy.orm.Query._has_entity = _has_entity
        sqlalchemy.orm.Query.unique_join = unique_join
        INIT = True
