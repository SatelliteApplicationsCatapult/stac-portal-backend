import datetime
from typing import Dict, Tuple

import geoalchemy2
import requests
from flask import Response
from shapely.geometry import box, MultiPolygon

from app.main.service import public_catalogs_service
from .. import db
from ..custom_exceptions import *
from ..model.private_catalog_model import PrivateCollection
from ..routes import route


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
    potential_datetime_formats = ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%dT%H:%M:%S.%f']
    try:
        temporal_extent_start = collection['extent']['temporal']['interval'][0][0]
        if temporal_extent_start == '..' or temporal_extent_start == '':
            temporal_extent_start = None
    except KeyError:
        temporal_extent_start = None
    try:
        temporal_extent_end = collection['extent']['temporal']['interval'][0][1]
        if temporal_extent_end == '..' or temporal_extent_end == '':
            temporal_extent_end = None
    except KeyError:
        temporal_extent_end = None
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
        if temporal_extent_start is not None:
            private_collection.temporal_extent_start = None
            for fmt in potential_datetime_formats:
                try:
                    private_collection.temporal_extent_start = datetime.datetime.strptime(temporal_extent_start, fmt)
                    break
                except ValueError:
                    continue
            if private_collection.temporal_extent_start is None:
                raise ConvertingTimestampError
        if temporal_extent_end is not None:
            private_collection.temporal_extent_end = None
            for fmt in potential_datetime_formats:
                try:
                    private_collection.temporal_extent_end = datetime.datetime.strptime(temporal_extent_end, fmt)
                    break
                except ValueError:
                    continue
            if private_collection.temporal_extent_end is None:
                raise ConvertingTimestampError
        bboxes = collection['extent']['spatial']['bbox']
        shapely_boxes = []
        for i in range(0, len(bboxes)):
            shapely_box = box(*(collection['extent']['spatial']['bbox'][i]))
            shapely_boxes.append(shapely_box)
        shapely_multi_polygon = geoalchemy2.shape.from_shape(MultiPolygon(shapely_boxes), srid=4326)
        private_collection.spatial_extent = shapely_multi_polygon
        db.session.add(private_collection)
        try:
            status = _create_new_collection_on_stac_api(collection)
            db.session.commit()
            return status
        except PrivateCollectionAlreadyExistsError:
            # it doesnt exist in database, but is present on stac server, store it in database
            # and update on stac-fastapi
            try:
                status = _update_existing_collection_on_stac_api(collection)
                db.session.commit()
                return status
            except PrivateCollectionDoesNotExistError:
                status = _create_new_collection_on_stac_api(collection)
                db.session.commit()
                return status
        except InvalidCollectionPayloadError:
            db.session.rollback()
            raise InvalidCollectionPayloadError


def _create_new_collection_on_stac_api(
        collection_data: Dict[str,
                              any]) -> dict[str, any]:
    """Create a new collection on the STAC API server.

    :param collection_data: Collection data to create.
    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.post(route("COLLECTIONS"), json=collection_data)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json

    elif response.status_code == 409:
        raise PrivateCollectionAlreadyExistsError

    elif response.status_code == 400:
        raise InvalidCollectionPayloadError


def _update_existing_collection_on_stac_api(
        collection_data: Dict[str,
                              any]) -> dict[str, any]:
    """Update an existing collection on the STAC API server.

    :param collection_data: Collection data to create.
    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.put(route("COLLECTIONS"), json=collection_data)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 400:
        raise InvalidCollectionPayloadError
    elif response.status_code == 404:
        raise PrivateCollectionDoesNotExistError


def _remove_collection_by_id_on_stac_api(
        collection_id: str) -> Tuple[Dict[str, any], int] or Response:
    """Remove a collection by ID from the STAC API server.

    Additionally, removes all stored search parameters associated with the collection.


    :param collection_id: Collection ID to remove.
    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.delete(route("COLLECTIONS") + collection_id)
    search_parameters_removed = public_catalogs_service.remove_search_params_for_collection_id(
        collection_id)
    if response.status_code in range(200, 203):
        collection_json = response.json()
        return {
                   "parameters": collection_json,
                   "search_parameters_removed": search_parameters_removed,
                   "status": "success",
               }, response.status_code

    else:
        return _send_error_response(response)


def _add_item_to_collection_on_stac_api(
        collection_id: str,
        item_data: Dict[str, any]) -> Tuple[Dict[str, any], int] or Response:
    """Add an item to a collection on the STAC API server.

    :param collection_id: Collection data to create.
    :param item_data: Item data to store
    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.post(route("COLLECTIONS") + collection_id + "/items",
                             json=item_data)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return {
                   "parameters": collection_json,
                   "status": "success",
               }, response.status_code

    else:
        return _send_error_response(response)


def _update_item_in_collection_on_stac_api(
        collection_id: str, item_id: str,
        item_data: Dict[str, any]) -> Tuple[Dict[str, any], int] or Response:
    """Update an item in a collection on the STAC API server.

    :param collection_id: Collection data to create.
    :param item_id: Id of the item to update
    :param item_data: Item data to store
    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.put(route("COLLECTIONS") + collection_id + "/items/" +
                            item_id,
                            json=item_data)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return {
                   "parameters": collection_json,
                   "status": "success",
               }, response.status_code

    else:
        return _send_error_response(response)


def _remove_item_from_collection_on_stac_api(
        collection_id: str,
        item_id: str) -> Tuple[Dict[str, any], int] or Response:
    """Remove an item from a collection on the STAC API server.

    :param collection_id: Collection data to create.
    :param item_id: Id of the item to remove
    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.delete(
        route("COLLECTIONS") + collection_id + "/items/" + item_id)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return {
                   "parameters": collection_json,
                   "status": "success",
               }, response.status_code

    if response.status_code == 403:
        return Response(response.text, response.status_code,
                        response.headers.items())
    else:
        return _send_error_response(response)


def _send_error_response(
        response: requests.models.Response
) -> Tuple[Dict[str, any], int] or Response:
    """Send an error response to the client.

    Returns either error message from stac-api server or a proxied error response.

    :param response: Response object from the STAC API server.
    :return: Tuple containing error message and status code.
    """
    if response.status_code == 403:
        return Response(response.text, response.status_code,
                        response.headers.items())
    else:
        return {
                   "stac_api_server_response": response.json(),
                   "stac_api_server_response_code": response.status_code,
                   "status": "failed"
               }, response.status_code
