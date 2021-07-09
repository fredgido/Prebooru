# APP/MODELS/ARTIST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from flask import url_for
from sqlalchemy.orm import aliased

# ##LOCAL IMPORTS
from .. import DB, SESSION
from ..sites import GetSiteDomain, GetSiteKey
from ..logical.utility import GetCurrentTime, ProcessUTCTimestring
from .base import JsonModel, RemoveKeys, DateTimeOrNull, IntOrNone, StrOrNone
from .artist_url import ArtistUrl
from .illust import Illust
from .label import Label
from .description import Description
from .post import Post
from .illust_url import IllustUrl
from .notation import Notation

# ##GLOBAL VARIABLES

ArtistNames = DB.Table(
    'artist_names',
    DB.Column('label_id', DB.Integer, DB.ForeignKey('label.id'), primary_key=True),
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
)

ArtistSiteAccounts = DB.Table(
    'artist_site_accounts',
    DB.Column('label_id', DB.Integer, DB.ForeignKey('label.id'), primary_key=True),
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
)

ArtistProfiles = DB.Table(
    'artist_profiles',
    DB.Column('description_id', DB.Integer, DB.ForeignKey('description.id'), primary_key=True),
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
)

ArtistNotations = DB.Table(
    'artist_notations',
    DB.Column('notation_id', DB.Integer, DB.ForeignKey('notation.id'), primary_key=True),
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
)

@dataclass
class Artist(JsonModel):
    id: int
    site_id: int
    site_artist_id: IntOrNone
    current_site_account: StrOrNone
    site_created: DateTimeOrNull
    site_accounts: List[lambda x: x['name']]
    names: List[lambda x: x['name']]
    profiles: List[lambda x: x['body']]
    webpages: List[lambda x: RemoveKeys(x, ['artist_id'])]
    active: bool
    requery: DateTimeOrNull
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = DB.Column(DB.Integer, primary_key=True)
    site_id = DB.Column(DB.Integer, nullable=False)
    site_artist_id = DB.Column(DB.Integer, nullable=True)
    current_site_account = DB.Column(DB.String(255), nullable=True)
    site_created = DB.Column(DB.DateTime(timezone=False), nullable=True)
    site_accounts = DB.relationship(Label, secondary=ArtistSiteAccounts, lazy='subquery', backref=DB.backref('account_artists', lazy=True))
    names = DB.relationship(Label, secondary=ArtistNames, lazy='subquery', backref=DB.backref('name_artists', lazy=True))
    profiles = DB.relationship(Description, secondary=ArtistProfiles, lazy='subquery', backref=DB.backref('artists', lazy=True))
    illusts = DB.relationship(Illust, lazy=True, backref=DB.backref('artist', lazy=True), cascade="all, delete")
    webpages = DB.relationship(ArtistUrl, backref='artist', lazy=True, cascade="all, delete")
    notations = DB.relationship(Notation, secondary=ArtistNotations, lazy=True, backref=DB.backref('artist', uselist=False, lazy=True))
    active = DB.Column(DB.Boolean, nullable=True)
    requery = DB.Column(DB.DateTime(timezone=False), nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)

    @property
    def recent_posts(self):
        if self._recent_posts is None:
            q = Post.query
            q = q.join(IllustUrl, Post.illust_urls).join(Illust).join(Artist).filter(Artist.id == self.id)
            q = q.order_by(Post.id.desc())
            q = q.limit(10)
            self._recent_posts = q.all()
        return self._recent_posts

    @property
    def illust_count(self):
        return Illust.query.filter_by(artist_id=self.id).count()

    @property
    def site_domain(self):
        return GetSiteDomain(self.site_id)

    @property
    def booru_search_url(self):
        return self._source.ArtistBooruSearchUrl(self)

    @property
    def show_url(self):
        return url_for("artist.show_html", id=self.id)

    @property
    def illust_search(self):
        return url_for("illust.index_html", **{'search[artist_id]': self.id})

    def delete(self):
        self.names.clear()
        self.profiles.clear()
        self.site_accounts.clear()
        DB.session.delete(self)
        DB.session.commit()

    _recent_posts = None

    @property
    def _source(self):
        if not hasattr(self, '__source'):
            from ..sources import DICT as SOURCEDICT
            site_key = GetSiteKey(self.site_id)
            self.__source = SOURCEDICT[site_key]
        return self.__source


    @staticmethod
    def searchable_attributes():
        basic_attributes = ['id', 'site_id', 'site_artist_id', 'site_created', 'current_site_account', 'active', 'created', 'updated', 'requery']
        relation_attributes = ['names', 'site_accounts', 'profiles', 'webpages', 'illusts', 'boorus']
        return basic_attributes + relation_attributes
