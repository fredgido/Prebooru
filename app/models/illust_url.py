# APP/MODELS/ILLUST_URL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
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
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String(255), nullable=False)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    order = db.Column(db.Integer, nullable=False)
    illust_id = db.Column(db.Integer, db.ForeignKey('illust.id'), nullable=False)
    active = db.Column(db.Boolean, nullable=False)

    @staticmethod
    def searchable_attributes():
        basic_attributes = ['id', 'site_id', 'url', 'width', 'height', 'order', 'illust_id', 'active']
        relation_attributes = ['illust', 'post']
        return basic_attributes + relation_attributes
