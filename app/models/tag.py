# APP/MODELS/TAG.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class Tag(JsonModel):
    id: int
    name: str
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.Unicode(255), nullable=False)

    @staticmethod
    def searchable_attributes():
        return ['id', 'name']
