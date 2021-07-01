# APP/MODELS/ILLUST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from flask import url_for
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import DB
from ..sites import GetSiteDomain, GetSiteKey
from .base import JsonModel, DateTimeOrNull, RemoveKeys, IntOrNone
from .tag import Tag
from .illust_url import IllustUrl
from .site_data import SiteData
from .description import Description
from .notation import Notation
from .pool_element import PoolIllust


# ##GLOBAL VARIABLES

# Many-to-many tables

IllustTags = DB.Table(
    'illust_tags',
    DB.Column('tag_id', DB.Integer, DB.ForeignKey('tag.id'), primary_key=True),
    DB.Column('illust_id', DB.Integer, DB.ForeignKey('illust.id'), primary_key=True),
)

IllustDescriptions = DB.Table(
    'illust_descriptions',
    DB.Column('description_id', DB.Integer, DB.ForeignKey('description.id'), primary_key=True),
    DB.Column('illust_id', DB.Integer, DB.ForeignKey('illust.id'), primary_key=True),
)

IllustNotations = DB.Table(
    'illust_notations',
    DB.Column('illust_id', DB.Integer, DB.ForeignKey('illust.id'), primary_key=True),
    DB.Column('notation_id', DB.Integer, DB.ForeignKey('notation.id'), primary_key=True),
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
    active: bool
    requery: DateTimeOrNull
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = DB.Column(DB.Integer, primary_key=True)
    site_id = DB.Column(DB.Integer, nullable=False)
    site_illust_id = DB.Column(DB.Integer, nullable=False)
    site_created = DB.Column(DB.DateTime(timezone=False), nullable=True)
    descriptions = DB.relationship(Description, secondary=IllustDescriptions, lazy='subquery', backref=DB.backref('illusts', lazy=True))
    tags = DB.relationship(Tag, secondary=IllustTags, lazy='subquery', backref=DB.backref('illusts', lazy=True))
    urls = DB.relationship(IllustUrl, backref='illust', lazy=True, cascade="all, delete")
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('artist.id'), nullable=False)
    pages = DB.Column(DB.Integer, nullable=True)
    score = DB.Column(DB.Integer, nullable=True)
    site_data = DB.relationship(SiteData, backref='illust', lazy=True, uselist=False, cascade="all, delete")
    notations = DB.relationship(Notation, secondary=IllustNotations, lazy=True, backref=DB.backref('illust', uselist=False, lazy=True), cascade='all,delete')
    _pools = DB.relationship(PoolIllust, backref='item', lazy=True, cascade='all,delete')
    pools = association_proxy('_pools', 'pool')
    posts = association_proxy('urls', 'post')
    active = DB.Column(DB.Boolean, nullable=True)
    requery = DB.Column(DB.DateTime(timezone=False), nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)

    @property
    def site_domain(self):
        return GetSiteDomain(self.site_id)

    @property
    def show_url(self):
        return url_for("illust.show_html", id=self.id)

    @property
    def type(self):
        if not hasattr(self, '__type'):
            if self._source.IllustHasVideos(self):
                self.__type = 'video'
            elif self._source.IllustHasImages(self):
                self.__type = 'image'
            else:
                self.__type =  'unknown'
        return self.__type

    @property
    def video_illust_url(self):
        if not hasattr(self, '__video_illust_url'):
            self.__video_illust_url = self._source.VideoIllustVideoUrl(self) if self.type == 'video' else None
        return self.__video_illust_url

    @property
    def thumb_illust_url(self):
        if not hasattr(self, '__thumb_illust_url'):
            self.__thumb_illust_url = self._source.VideoIllustThumbUrl(self) if self.type == 'video' else None
        return self.__thumb_illust_url

    @property
    def _source(self):
        if not hasattr(self, '__source'):
            from ..sources import DICT as SOURCEDICT
            site_key = GetSiteKey(self.site_id)
            self.__source = SOURCEDICT[site_key]
        return self.__source

    def delete(self):
        pools = self.pools
        DB.session.delete(self)
        DB.session.commit()
        for pool in pools:
            pool._elements.reorder()
        if len(pools) > 0:
            DB.session.commit()
    
    @staticmethod
    def searchable_attributes():
        basic_attributes = ['id', 'site_id', 'site_illust_id', 'site_created', 'artist_id', 'pages', 'score', 'active', 'created', 'updated', 'requery']
        relation_attributes = ['artist', 'urls', 'tags', 'descriptions', 'notations']
        return basic_attributes + relation_attributes
