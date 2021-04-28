# APP/MODELS/ILLUST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel, DateTimeOrNull, RemoveKeys
from .tag import Tag
from .illust_url import IllustUrl
from .site_data import SiteData


# ##GLOBAL VARIABLES

# Many-to-many tables

IllustTags = db.Table(
    'illust_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('illust_id', db.Integer, db.ForeignKey('illust.id'), primary_key=True),
)


# Classes


@dataclass
class Illust(JsonModel):
    id: int
    site_id: int
    site_illust_id: int
    site_created: DateTimeOrNull
    description: str
    tags: List[lambda x: x['name']]
    urls: List[lambda x: RemoveKeys(x, ['id', 'illust_id'])]
    artist_id: int
    pages: int
    score: int
    site_data: lambda x: RemoveKeys(x.to_json(), ['id', 'illust_id', 'type'])
    requery: DateTimeOrNull
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, nullable=False)
    site_illust_id = db.Column(db.Integer, nullable=False)
    site_created = db.Column(db.DateTime(timezone=False), nullable=True)
    description = db.Column(db.UnicodeText, nullable=True)
    tags = db.relationship(Tag, secondary=IllustTags, lazy='subquery', backref=db.backref('illusts', lazy=True))
    urls = db.relationship(IllustUrl, backref='illust', lazy=True, cascade="all, delete")
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    pages = db.Column(db.Integer, nullable=True)
    score = db.Column(db.Integer, nullable=True)
    site_data = db.relationship(SiteData, backref='illust', lazy=True, uselist=False, cascade="all, delete")
    requery = db.Column(db.DateTime(timezone=False), nullable=True)
    created = db.Column(db.DateTime(timezone=False), nullable=False)
    updated = db.Column(db.DateTime(timezone=False), nullable=False)
