# APP/MODELS/ARTIST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel, RemoveKeys, DateTimeOrNull, IntOrNone, StrOrNone
from .artist_url import ArtistUrl
from .illust import Illust


# ##GLOBAL VARIABLES


@dataclass
class Artist(JsonModel):
    id: int
    site_id: int
    site_artist_id: IntOrNone
    site_account: StrOrNone
    name: str
    profile: str
    webpages: List[lambda x: RemoveKeys(x, ['artist_id'])]
    requery: DateTimeOrNull
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, nullable=False)
    site_artist_id = db.Column(db.Integer, nullable=True)
    site_account = db.Column(db.String(255), nullable=True)
    name = db.Column(db.Unicode(255), nullable=False)
    profile = db.Column(db.UnicodeText, nullable=False)
    illusts = db.relationship(Illust, lazy=True, backref=db.backref('artist', lazy=True))
    webpages = db.relationship(ArtistUrl, backref='artist', lazy=True)
    requery = db.Column(db.DateTime(timezone=False), nullable=True)
    created = db.Column(db.DateTime(timezone=False), nullable=False)
    updated = db.Column(db.DateTime(timezone=False), nullable=False)
