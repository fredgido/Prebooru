# APP/MODELS/UPLOAD_URL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class UploadUrl(JsonModel):
    id: int
    url: str
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
