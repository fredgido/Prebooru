# APP/MODELS/ILLUST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from flask import url_for
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import db
from ..sites import GetSiteDomain, GetSiteKey
from .base import JsonModel, DateTimeOrNull, RemoveKeys, IntOrNone
from .tag import Tag
from .illust_url import IllustUrl
from .site_data import SiteData
from .description import Description
from .pool_element import PoolIllust


# ##GLOBAL VARIABLES

# Many-to-many tables

IllustTags = db.Table(
    'illust_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('illust_id', db.Integer, db.ForeignKey('illust.id'), primary_key=True),
)

IllustDescriptions = db.Table(
    'illust_descriptions',
    db.Column('description_id', db.Integer, db.ForeignKey('description.id'), primary_key=True),
    db.Column('illust_id', db.Integer, db.ForeignKey('illust.id'), primary_key=True),
)


# Classes


@dataclass
class Illust(JsonModel):
    id: int
    site_id: int
    site_illust_id: int
    site_created: DateTimeOrNull
    descriptions: List[lambda x: x['body']]
    tags: List[lambda x: x['name']]
    urls: List[lambda x: RemoveKeys(x, ['id', 'illust_id'])]
    artist_id: int
    pages: int
    score: IntOrNone
    site_data: lambda x: RemoveKeys(x.to_json(), ['id', 'illust_id', 'type'])
    requery: DateTimeOrNull
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, nullable=False)
    site_illust_id = db.Column(db.Integer, nullable=False)
    site_created = db.Column(db.DateTime(timezone=False), nullable=True)
    descriptions = db.relationship(Description, secondary=IllustDescriptions, lazy='subquery', backref=db.backref('illusts', lazy=True))
    tags = db.relationship(Tag, secondary=IllustTags, lazy='subquery', backref=db.backref('illusts', lazy=True))
    urls = db.relationship(IllustUrl, backref='illust', lazy=True, cascade="all, delete")
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    pages = db.Column(db.Integer, nullable=True)
    score = db.Column(db.Integer, nullable=True)
    site_data = db.relationship(SiteData, backref='illust', lazy=True, uselist=False, cascade="all, delete")
    _pools = db.relationship(PoolIllust, backref='item', lazy=True, cascade='all,delete')
    pools = association_proxy('_pools', 'pool')
    requery = db.Column(db.DateTime(timezone=False), nullable=True)
    created = db.Column(db.DateTime(timezone=False), nullable=False)
    updated = db.Column(db.DateTime(timezone=False), nullable=False)

    @property
    def site_domain(self):
        return GetSiteDomain(self.site_id)

    @property
    def show_url(self):
        return url_for("illust.show_html", id=self.id)

    @property
    def type(self):
        if self._source.IllustHasVideos(self):
            return 'video'
        if self._source.IllustHasImages(self):
            return 'image'
        return 'unknown'

    @property
    def _source(self):
        from ..sources import DICT as SOURCEDICT
        site_key = GetSiteKey(self.site_id)
        return SOURCEDICT[site_key]
