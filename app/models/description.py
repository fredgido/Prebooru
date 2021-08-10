# APP/MODELS/DESCRIPTION.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class Description(JsonModel):
    id: int
    body: str
    id = DB.Column(DB.Integer, primary_key=True)
    body = DB.Column(DB.UnicodeText, nullable=False)

    @staticmethod
    def searchable_attributes():
        return ['id', 'body']
