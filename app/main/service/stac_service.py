from typing import Dict, Tuple

import requests
from flask import Response

from . import public_catalogs_service
from ..custom_exceptions import InvalidCollectionPayloadError, PrivateCollectionDoesNotExistError, \
    PrivateCollectionAlreadyExistsError
from ..routes import route


def get_all_collections() -> Tuple[Dict[str, any], int] or Response:
    """Get all collections from the STAC API server.

    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.get(route("COLLECTIONS"))

    if response.status_code in range(200, 203):
        collection_json = response.json()
        collection_count = len(collection_json["collections"])
        return {
                   "parameters": collection_json,
                   "count": collection_count,
                   "status": "success",
               }, response.status_code

    else:
        return send_error_response(response)


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


def get_collection_by_id(
        collection_id: str) -> Tuple[Dict[str, any], int] or Response:
    """Get a collection by ID from the STAC API server.

    :return: Either a tuple containing stac server response and status code, or a Response object.
    :param collection_id: Collection ID to get.
    :return:
    """
    response = requests.get(route("COLLECTIONS") + collection_id)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return {
                   "parameters": collection_json,
                   "status": "success",
               }, response.status_code

    else:
        return send_error_response(response)


def get_items_by_collection_id(
        collection_id: str) -> Tuple[Dict[str, any], int] or Response:
    """Get all items from a collection on the STAC API server.

    :param collection_id: Collection id to get items from.
    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.get(route("COLLECTIONS") + collection_id + "/items")

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return {
                   "parameters": collection_json,
                   "status": "success",
               }, response.status_code

    else:
        return send_error_response(response)


def get_item_from_collection(
        collection_id: str,
        item_id: str) -> Tuple[Dict[str, any], int] or Response:
    response = requests.get(
        route("COLLECTIONS") + collection_id + "/items/" + item_id)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return {
                   "parameters": collection_json,
                   "status": "success",
               }, response.status_code

    else:
        return send_error_response(response)


def create_new_collection_on_stac_api(
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


def update_existing_collection_on_stac_api(
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


def remove_public_collection_by_id_on_stac_api(
        collection_id: str) -> Dict[str, any]:
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
        return collection_json
    elif response.status_code == 400:
        raise InvalidCollectionPayloadError
    elif response.status_code == 404:
        raise PrivateCollectionDoesNotExistError


def remove_private_collection_by_id_on_stac_api(collection_id: str) -> Dict[str, any]:
    response = requests.delete(route("COLLECTIONS") + collection_id)
    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 400:
        raise InvalidCollectionPayloadError
    elif response.status_code == 404:
        raise PrivateCollectionDoesNotExistError
    pass


def add_item_to_collection_on_stac_api(
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
        return send_error_response(response)


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
        return send_error_response(response)


def remove_item_from_collection_on_stac_api(
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
        return send_error_response(response)
