# APP/CACHE/API_DATA.PY

# ##PYTHON IMPORTS

# ##LOCAL IMPORTS
from .. import db

# ##GLOBAL VARIABLES

class ApiData(db.Model):
    __bind_key__ = 'cache'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(255), nullable=False)
    site_id = db.Column(db.Integer, nullable=False)
    data_id = db.Column(db.Integer, nullable=False)
    data = db.Column(db.JSON, nullable=False)
    expires = db.Column(db.DateTime(timezone=False), nullable=False)
