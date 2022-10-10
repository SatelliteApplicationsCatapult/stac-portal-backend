import datetime
from typing import Dict

import geoalchemy2
from shapely.geometry import box, MultiPolygon

from .stac_service import update_existing_collection_on_stac_api, create_new_collection_on_stac_api
from .. import db
from ..custom_exceptions import *
from ..model.private_catalog_model import PrivateCollection
from ..util.process_timestamp import *


def _does_collection_exist_in_database(collection_id: str) -> bool:
    """Check if a collection exists in the database.

    :param collection_id: Collection ID to check.
    :return: True if collection exists, False otherwise.
    """
    return PrivateCollection.query.filter_by(id=collection_id).first() is not None


def add_collection(collection: Dict[str, any]) -> Dict[str, any]:
    collection_id = collection["id"]
    if _does_collection_exist_in_database(collection_id):
        raise PrivateCollectionAlreadyExistsError

    if True:
        private_collection = PrivateCollection()
        private_collection.id = collection_id
        try:
            private_collection.type = collection['type']
        except KeyError:
            private_collection.type = "Collection"
        try:
            private_collection.title = collection['title']
        except KeyError:
            private_collection.title = None
        try:
            private_collection.description = collection['description']
        except KeyError:
            private_collection.description = None

        bboxes = collection['extent']['spatial']['bbox']
        shapely_boxes = []
        for i in range(0, len(bboxes)):
            shapely_box = box(*(collection['extent']['spatial']['bbox'][i]))
            shapely_boxes.append(shapely_box)
        shapely_multi_polygon = geoalchemy2.shape.from_shape(MultiPolygon(shapely_boxes), srid=4326)
        private_collection.spatial_extent = shapely_multi_polygon
        temporal_extent_start = collection['extent']['temporal']['interval'][0][0]
        temporal_extent_end = collection['extent']['temporal']['interval'][0][1]
        private_collection.temporal_extent_start = process_timestamp_single_string(temporal_extent_start)
        private_collection.temporal_extent_end = process_timestamp_single_string(temporal_extent_end)
        db.session.add(private_collection)
        try:
            status = create_new_collection_on_stac_api(collection)
            db.session.commit()
            return status
        except PrivateCollectionAlreadyExistsError:
            # it doesnt exist in database, but is present on stac server, store it in database
            # and update on stac-fastapi
            status = update_existing_collection_on_stac_api(collection)
            db.session.commit()
            return status
        except InvalidCollectionPayloadError:
            db.session.rollback()
            raise InvalidCollectionPayloadError


def update_collection(collection: Dict[str, any]) -> Dict[str, any]:
    collection_id = collection["id"]
    if not _does_collection_exist_in_database(collection_id):
        raise PrivateCollectionDoesNotExistError
    private_collection = PrivateCollection.query.filter_by(id=collection_id).first()
    try:
        private_collection.title = collection['title']
    except KeyError:
        pass
    private_collection.description = collection['description']
    bboxes = collection['extent']['spatial']['bbox']
    shapely_boxes = []
    for i in range(0, len(bboxes)):
        shapely_box = box(*(collection['extent']['spatial']['bbox'][i]))
        shapely_boxes.append(shapely_box)
    shapely_multi_polygon = geoalchemy2.shape.from_shape(MultiPolygon(shapely_boxes), srid=4326)
    private_collection.spatial_extent = shapely_multi_polygon
    temporal_extent_start = collection['extent']['temporal']['interval'][0][0]
    temporal_extent_end = collection['extent']['temporal']['interval'][0][1]
    private_collection.temporal_extent_start = process_timestamp_single_string(temporal_extent_start)
    private_collection.temporal_extent_end = process_timestamp_single_string(temporal_extent_end)
    try:
        status = update_existing_collection_on_stac_api(collection)
        db.session.commit()
        return status
    except PrivateCollectionDoesNotExistError:
        status = create_new_collection_on_stac_api(collection)
        db.session.commit()
        return status
    except InvalidCollectionPayloadError:
        db.session.rollback()
        raise InvalidCollectionPayloadError




