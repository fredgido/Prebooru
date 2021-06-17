# APP/MODELS/LABEL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class Label(JsonModel):
    id: int
    name: str
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)

    @staticmethod
    def searchable_attributes():
        return ['id', 'name']
