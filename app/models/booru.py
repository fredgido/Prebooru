# APP/MODELS/ARTIST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from flask import url_for
from sqlalchemy.orm import aliased
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import db
from ..sites import GetSiteDomain
from .base import JsonModel, RemoveKeys, DateTimeOrNull, IntOrNone, StrOrNone
from .artist import Artist
from .artist_url import ArtistUrl
from .illust import Illust
from .label import Label
from .description import Description
from .post import Post
from .illust_url import IllustUrl

# ##GLOBAL VARIABLES

BooruNames = db.Table(
    'booru_names',
    db.Column('label_id', db.Integer, db.ForeignKey('label.id'), primary_key=True),
    db.Column('booru_id', db.Integer, db.ForeignKey('booru.id'), primary_key=True),
)

BooruArtists = db.Table(
    'booru_artists',
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True),
    db.Column('booru_id', db.Integer, db.ForeignKey('booru.id'), primary_key=True),
)


@dataclass
class Booru(JsonModel):
    id: int
    danbooru_id: int
    current_name: str
    names: List[lambda x: x['name']]
    artist_ids: List
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = db.Column(db.Integer, primary_key=True)
    danbooru_id = db.Column(db.Integer, nullable=False)
    current_name = db.Column(db.String(255), nullable=False)
    names = db.relationship(Label, secondary=BooruNames, lazy=True, backref=db.backref('boorus', lazy=True))
    artists = db.relationship(Artist, secondary=BooruArtists, backref='boorus', lazy=True)
    created = db.Column(db.DateTime(timezone=False), nullable=False)
    updated = db.Column(db.DateTime(timezone=False), nullable=False)

    artist_ids = association_proxy('artists', 'id')

    @property
    def recent_posts(self):
        if not hasattr(self, '_recent_posts'):
            q = Post.query
            q = q.join(IllustUrl, Post.illust_urls).join(Illust).join(Artist).join(Booru).filter(Booru.id == self.id)
            q = q.order_by(Post.id.desc())
            q = q.limit(10)
            self._recent_posts = q.all()
        return self._recent_posts

    @property
    def show_url(self):
        return url_for("booru.show_html", id=self.id)

    def delete(self):
        self.names.clear()
        self.artists.clear()
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def searchable_attributes():
        basic_attributes = ['id', 'danbooru_id', 'current_name', 'names', 'created', 'updated']
        relation_attributes = ['names', 'artists']
        return basic_attributes + relation_attributes
