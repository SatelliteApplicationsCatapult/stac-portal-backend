import datetime

from geoalchemy2 import Geometry

from .. import db


class PublicCatalog(db.Model):
    __tablename__ = "public_catalogs"
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name: str = db.Column(db.Text, nullable=False)
    url: str = db.Column(db.Text, nullable=False, unique=True)
    description: str = db.Column(db.Text, nullable=True)
    added_on: datetime.datetime = db.Column(db.DateTime,
                                            nullable=False,
                                            default=datetime.datetime.utcnow)
    stored_search_parameters = db.relationship("StoredSearchParameters", backref="public_catalogs", lazy="dynamic",
                                               cascade="all, delete-orphan")
    stored_ingestion_statuses = db.relationship("StacIngestionStatus", backref="public_catalogs", lazy="dynamic",
                                                cascade="all, delete-orphan")
    collections = db.relationship("PublicCollection", backref="public_catalogs", lazy="dynamic",
                                  cascade="all, delete-orphan")

    def get_number_of_stored_search_parameters(self):
        return StoredSearchParameters.query.filter_by(
            associated_catalog_id=self.id).count()

    def as_dict(self):
        data = {
            c.name: str(getattr(self, c.name))
            for c in self.__table__.columns
        }

        data[
            "number_of_stored_search_parameters_associated"] = self.get_number_of_stored_search_parameters(
        )
        return data


class PublicCollection(db.Model):
    __tablename__ = "public_collections"
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False, default="Collection")
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    temporal_extent_start = db.Column(db.DateTime, nullable=True, default=None)
    temporal_extent_end = db.Column(db.DateTime, nullable=True, default=None)
    spatial_extent = db.Column(Geometry(geometry_type="MULTIPOLYGON"), nullable=True, default=None)
    parent_catalog = db.Column(db.Integer, db.ForeignKey("public_catalogs.id", ondelete='CASCADE'), nullable=False)


class StoredSearchParameters(db.Model):
    __tablename__ = "stored_search_parameters"
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bbox = db.Column(db.Text, nullable=True, default="[]")
    datetime = db.Column(db.Text, nullable=True, default="")
    collection = db.Column(db.Text, nullable=True, default="")
    used_search_parameters: str = db.Column(db.Text,
                                            nullable=False,
                                            unique=True)
    associated_catalog_id: int = db.Column(db.Integer,
                                           db.ForeignKey('public_catalogs.id',
                                                         ondelete='CASCADE'),
                                           nullable=False,
                                           index=True)
