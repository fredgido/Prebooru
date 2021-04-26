# APP/MODELS/ERROR.PY

# ##PYTHON IMPORTS
import datetime
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class Error(JsonModel):
    id: int
    module: str
    message: str
    created: datetime.datetime.isoformat
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(255), nullable=False)
    message = db.Column(db.UnicodeText, nullable=False)
    created = db.Column(db.DateTime(timezone=False), nullable=False)
