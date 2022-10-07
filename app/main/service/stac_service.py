from typing import Dict, Tuple

import requests
from flask import Response

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
        return _send_error_response(response)


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
        return _send_error_response(response)


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
        return _send_error_response(response)
