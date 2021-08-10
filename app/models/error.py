# APP/MODELS/ERROR.PY

# ##PYTHON IMPORTS
import datetime
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class Error(JsonModel):
    id: int
    module: str
    message: str
    created: datetime.datetime.isoformat
    id = DB.Column(DB.Integer, primary_key=True)
    module = DB.Column(DB.String(255), nullable=False)
    message = DB.Column(DB.UnicodeText, nullable=False)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)

    @staticmethod
    def searchable_attributes():
        return ['id', 'module', 'message', 'created']
