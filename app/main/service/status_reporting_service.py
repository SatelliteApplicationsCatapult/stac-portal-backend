import datetime
from typing import Dict, Tuple, List

from app.main.model.public_catalogs_model import PublicCatalog
from .. import db
from ..model.status_reporting_model import StacIngestionStatus


def get_all_stac_ingestion_statuses() -> List[Dict[any, any]]:
    a: StacIngestionStatus = StacIngestionStatus.query.all()
    return [i.as_dict() for i in a]


def get_stac_ingestion_status_by_id(id: str) -> Dict[any, any]:
    a: StacIngestionStatus = StacIngestionStatus.query.filter_by(id=id).first()
    return a.as_dict()


def _make_stac_ingestion_status_entry(source_stac_api_url: str,
                                      target_stac_api_url: str,
                                      update: bool) -> int:
    print("source_stac_api_url: ", source_stac_api_url)
    public_catalogue_entry: PublicCatalog = PublicCatalog.query.filter(
        PublicCatalog.url == source_stac_api_url).first()

    if public_catalogue_entry is None:
        raise ValueError("Target STAC API URL not found in public catalogs.")
    # stac_search_parameters: StoredSearchParameters = StoredSearchParameters()
    # stac_search_parameters.associated_catalog_id = public_catalogue_entry.id
    stac_ingestion_status: StacIngestionStatus = StacIngestionStatus()
    stac_ingestion_status.source_stac_api_url = source_stac_api_url
    stac_ingestion_status.target_stac_api_url = target_stac_api_url
    stac_ingestion_status.update = update
    stac_ingestion_status.time_started = datetime.datetime.utcnow()
    db.session.add(stac_ingestion_status)
    db.session.commit()
    return stac_ingestion_status.id


def set_stac_ingestion_status_entry(
        status_id: str, newly_stored_collections_count: int,
        newly_stored_collections: List[str], updated_collections_count: int,
        updated_collections: List[str], newly_stored_items_count: int,
        updated_items_count: int,
        already_stored_items_count: int) -> Tuple[Dict[any, any]]:
    # get StacIngestionStatus object with id = status_id
    a: StacIngestionStatus = StacIngestionStatus.query.get(status_id)
    # update the object
    a.newly_stored_collections_count = newly_stored_collections_count
    a.newly_stored_collections = ",".join(newly_stored_collections)
    a.updated_collections_count = updated_collections_count
    a.updated_collections = ",".join(updated_collections)
    a.newly_stored_items_count = newly_stored_items_count
    a.updated_items_count = updated_items_count
    a.already_stored_items_count = already_stored_items_count
    a.time_finished = datetime.datetime.utcnow()

    db.session.add(a)
    db.session.commit()
    return a.as_dict()


def remove_stac_ingestion_status_entry(
        status_id: str) -> Tuple[Dict[any, any]]:
    a: StacIngestionStatus = StacIngestionStatus.query.filter_by(
        id=status_id).first()
    db.session.delete(a)
    db.session.commit()
    return a.as_dict()
