# APP/CACHE/API_DATA.PY

# ##LOCAL IMPORTS
from .. import DB

# ##GLOBAL VARIABLES

class ApiData(DB.Model):
    __bind_key__ = 'cache'
    id = DB.Column(DB.Integer, primary_key=True)
    type = DB.Column(DB.String(255), nullable=False)
    site_id = DB.Column(DB.Integer, nullable=False)
    data_id = DB.Column(DB.Integer, nullable=False)
    data = DB.Column(DB.JSON, nullable=False)
    expires = DB.Column(DB.DateTime(timezone=False), nullable=False)
