# APP/MODELS/ILLUST_URL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB
from .base import JsonModel, IntOrNone


# ##GLOBAL VARIABLES


@dataclass
class IllustUrl(JsonModel):
    id: int
    site_id: int
    url: str
    width: IntOrNone
    height: IntOrNone
    order: int
    illust_id: int
    active: bool
    id = DB.Column(DB.Integer, primary_key=True)
    site_id = DB.Column(DB.Integer, nullable=False)
    url = DB.Column(DB.String(255), nullable=False)
    width = DB.Column(DB.Integer, nullable=True)
    height = DB.Column(DB.Integer, nullable=True)
    order = DB.Column(DB.Integer, nullable=False)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)

    @staticmethod
    def searchable_attributes():
        basic_attributes = ['id', 'site_id', 'url', 'width', 'height', 'order', 'illust_id', 'active']
        relation_attributes = ['illust', 'post']
        return basic_attributes + relation_attributes
