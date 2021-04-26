# APP/MODELS/SITE_DATA.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass
from sqlalchemy.orm import declared_attr

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel, DateTimeOrNull


# ##GLOBAL VARIABLES


@dataclass
class SiteData(JsonModel):
    __tablename__ = 'site_data'
    id: int
    illust_id: int
    type: str
    id = db.Column(db.Integer, primary_key=True)
    illust_id = db.Column(db.Integer, db.ForeignKey('illust.id'), nullable=False)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'site_data',
        "polymorphic_on": type
    }


@dataclass
class PixivData(SiteData):
    __tablename__ = 'pixiv_data'
    site_uploaded: DateTimeOrNull
    site_updated: DateTimeOrNull
    title: str
    bookmarks: int
    replies: int
    views: int
    site_uploaded = db.Column(db.DateTime(timezone=False), nullable=True)
    site_updated = db.Column(db.DateTime(timezone=False), nullable=True)
    title = db.Column(db.UnicodeText, nullable=True)
    bookmarks = db.Column(db.Integer, nullable=True)
    views = db.Column(db.Integer, nullable=True)

    @declared_attr
    def replies(cls):
        return SiteData.__table__.c.get('replies', db.Column(db.Integer, nullable=True))

    __mapper_args__ = {
        'polymorphic_identity': 'pixiv_data',
    }


@dataclass
class TwitterData(SiteData):
    __tablename__ = 'twitter_data'
    retweets: int
    replies: int
    quotes: int
    retweets = db.Column(db.Integer, nullable=True)
    quotes = db.Column(db.Integer, nullable=True)

    @declared_attr
    def replies(cls):
        return SiteData.__table__.c.get('replies', db.Column(db.Integer, nullable=True))

    __mapper_args__ = {
        'polymorphic_identity': 'twitter_data',
    }
