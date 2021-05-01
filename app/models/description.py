# APP/MODELS/DESCRIPTION.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class Description(JsonModel):
    id: int
    body: str
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.UnicodeText, nullable=False)
