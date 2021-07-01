# APP/MODELS/UPLOAD_URL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class UploadUrl(JsonModel):
    id: int
    url: str
    id = DB.Column(DB.Integer, primary_key=True)
    url = DB.Column(DB.String(255), nullable=False)

    @staticmethod
    def searchable_attributes():
        return ['id', 'url']
