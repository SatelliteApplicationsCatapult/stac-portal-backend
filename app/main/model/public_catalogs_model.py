import datetime

from .. import db


class PublicCatalog(db.Model):
    __tablename__ = "public_catalogs"
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name: str = db.Column(db.Text, nullable=False)
    url: str = db.Column(db.Text, nullable=False, unique=True)
    description: str = db.Column(db.Text, nullable=True)
    stac_version: str = db.Column(db.Text, nullable=True)
    added_on: datetime.datetime = db.Column(db.DateTime,
                                            nullable=False,
                                            default=datetime.datetime.utcnow)

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


class StoredSearchParameters(db.Model):
    __tablename__ = "stored_search_parameters"
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    associated_catalog_id: int = db.Column(db.Integer,
                                           db.ForeignKey('public_catalogs.id'),
                                           nullable=False)
    used_search_parameters: str = db.Column(db.Text,
                                            nullable=False,
                                            unique=True)