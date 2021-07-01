# APP/CACHE/API_DATA.PY

# ##LOCAL IMPORTS
from .. import DB

# ##GLOBAL VARIABLES

class Domain(DB.Model):
    __bind_key__ = 'cache'
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(255), nullable=False)
    redirector = DB.Column(DB.Boolean, nullable=False)