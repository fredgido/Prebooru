# APP/MODELS/SUBSCRIPTION.PY

# ##PYTHON IMPORTS
import datetime
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import db
from .base import JsonModel, DateTimeOrNull


# ##GLOBAL VARIABLES


@dataclass
class Subscription(JsonModel):
    id: int
    artist_id: int
    # user_id: int
    requery: DateTimeOrNull
    created: datetime.datetime.isoformat
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, nullable=False)
    # user_id = db.Column(db.Integer, nullable=True)
    uploads = db.relationship('Upload', backref='subscription', lazy=True)
    requery = db.Column(db.DateTime(timezone=False), nullable=True)
    created = db.Column(db.DateTime(timezone=False), nullable=False)
