# APP/MODELS/ARTIST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from flask import url_for
from sqlalchemy.orm import aliased

# ##LOCAL IMPORTS
from .. import db
from ..sites import GetSiteDomain
from .base import JsonModel, RemoveKeys, DateTimeOrNull, IntOrNone, StrOrNone
from .artist_url import ArtistUrl
from .illust import Illust
from .label import Label
from .description import Description
from .post import Post
from .illust_url import IllustUrl

# ##GLOBAL VARIABLES

ArtistNames = db.Table(
    'artist_names',
    db.Column('label_id', db.Integer, db.ForeignKey('label.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True),
)

ArtistSiteAccounts = db.Table(
    'artist_site_accounts',
    db.Column('label_id', db.Integer, db.ForeignKey('label.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True),
)

ArtistProfiles = db.Table(
    'artist_profiles',
    db.Column('description_id', db.Integer, db.ForeignKey('description.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True),
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
    requery: DateTimeOrNull
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, nullable=False)
    site_artist_id = db.Column(db.Integer, nullable=True)
    current_site_account = db.Column(db.String(255), nullable=True)
    site_created = db.Column(db.DateTime(timezone=False), nullable=True)
    site_accounts = db.relationship(Label, secondary=ArtistSiteAccounts, lazy='subquery', backref=db.backref('account_artists', lazy=True))
    names = db.relationship(Label, secondary=ArtistNames, lazy='subquery', backref=db.backref('name_artists', lazy=True))
    profiles = db.relationship(Description, secondary=ArtistProfiles, lazy='subquery', backref=db.backref('artists', lazy=True))
    illusts = db.relationship(Illust, lazy=True, backref=db.backref('artist', lazy=True), cascade="all, delete")
    webpages = db.relationship(ArtistUrl, backref='artist', lazy=True, cascade="all, delete")
    requery = db.Column(db.DateTime(timezone=False), nullable=True)
    created = db.Column(db.DateTime(timezone=False), nullable=False)
    updated = db.Column(db.DateTime(timezone=False), nullable=False)

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
    def site_domain(self):
        return GetSiteDomain(self.site_id)

    @property
    def show_url(self):
        return url_for("artist.show_html", id=self.id)

    def delete(self):
        self.names.clear()
        self.profiles.clear()
        self.site_accounts.clear()
        db.session.delete(self)
        db.session.commit()

    _recent_posts = None

#Including these so that joins on both can be disambiguated (see notes)

Names = aliased(Label)
SiteAccounts = aliased(Label)
