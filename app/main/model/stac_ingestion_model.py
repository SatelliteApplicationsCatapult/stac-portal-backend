from email.policy import default
from math import fabs
from .. import db, flask_bcrypt
import flask_sqlalchemy.model
from flask_sqlalchemy import SQLAlchemy
import datetime
from ..config import key
import jwt
from typing import Union
from flask_sqlalchemy.model import DefaultMeta


class StacIngestionStatus(db.Model):
    __tablename__ = "stac_ingestion_status"
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time_started: datetime.datetime = db.Column(db.DateTime, nullable=True, default=datetime.datetime.utcnow)
    time_finished: datetime.datetime = db.Column(db.DateTime, nullable=True)
    source_stac_api_url: str = db.Column(db.Text, nullable=True)
    target_stac_api_url: str = db.Column(db.Text, nullable=True)
    update: bool = db.Column(db.Boolean, default=False)
    newly_stored_collections_count: int = db.Column(db.Integer,
                                                    nullable=True,
                                                    default=0)
    newly_stored_collections: str = db.Column(db.Text, nullable=True, default="")
    updated_collections_count: int = db.Column(db.Integer, nullable=True, default=0)
    updated_collections: str = db.Column(db.Text, nullable=True, default="")
    newly_stored_items_count: int = db.Column(db.Integer, nullable=True, default=0)
    updated_items_count: int = db.Column(db.Integer, nullable=True, default=0)
    already_stored_items_count: int = db.Column(db.Integer,
                                                nullable=True,
                                                default=0)

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}
