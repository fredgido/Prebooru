# APP/MODELS/ARTIST_URL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class ArtistUrl(JsonModel):
    id: int
    artist_id: int
    url: str
    active: bool
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
