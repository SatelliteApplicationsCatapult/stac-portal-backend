from typing import Dict, Tuple

import requests
from flask import Response

from app.main.service import public_catalogs_service
from ..routes import route


def get_all_collections() -> Tuple[Dict[str, str], int] or Response:
    """Get all collections from the STAC API server.

    Returns all records if STAC API server returns 200.
    Returns error message if STAC API server returns 4xx (but not 403).

    If any other status code is returned, the response is proxied to the client for easier debugging.
    (That probably means Azure configuration is bad, VPN is not used, etc.)

    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.get(route("COLLECTIONS"))

    if response.status_code == 200:
        collection_json = response.json()
        collection_count = len(collection_json["collections"])
        return {
            "parameters": collection_json,
            "count": collection_count,
            "status": "success",
        }, response.status_code

    if 404 <= response.status_code <= 499 or 400 <= response.status_code <= 402:
        return {
            "stac_api_server_response": response.json(),
            "stac_api_server_response_code": response.status_code,
            "status": "failed"
        }, response.status_code
    else:
        return Response(response.text, response.status_code,
                        response.headers.items())


def get_collection_by_id(
        collection_id: str) -> Tuple[Dict[str, str], int] or Response:
    """Get a collection by ID from the STAC API server.

    Returns all records if STAC API server returns 200.
    Returns error message if STAC API server returns 4xx (but not 403).

    If any other status code is returned, the response is proxied to the client for easier debugging.
    (That probably means Azure configuration is bad, VPN is not used, etc.)

    :return: Either a tuple containing stac server response and status code, or a Response object.
    :param collection_id: Collection ID to get.
    :return:
    """
    response = requests.get(route("COLLECTIONS") + collection_id)

    if response.status_code == 200:
        collection_json = response.json()
        return {
            "parameters": collection_json,
            "status": "success",
        }, response.status_code

    if 404 <= response.status_code <= 499 or 400 <= response.status_code <= 402:
        return {
            "stac_api_server_response": response.json(),
            "stac_api_server_response_code": response.status_code,
            "status": "failed"
        }, response.status_code
    else:
        return Response(response.text, response.status_code,
                        response.headers.items())


def remove_collection_by_id(
        collection_id: str) -> Tuple[Dict[str, str], int] or Response:
    """Remove a collection by ID from the STAC API server.

    Additionally, removes all stored search parameters associated with the collection.

    Returns removed collection if STAC API server returns 200.
    Returns error message if STAC API server returns 4xx (but not 403).

    If any other status code is returned, the response is proxied to the client for easier debugging.
    (That probably means Azure configuration is bad, VPN is not used, etc.)

    :param collection_id: Collection ID to remove.
    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.delete(route("COLLECTIONS") + collection_id)
    search_parameters_removed = public_catalogs_service.remove_search_params_for_collection_id(
        collection_id)
    if response.status_code == 200:
        collection_json = response.json()
        return {
            "parameters": collection_json,
            "search_parameters_removed": search_parameters_removed,
            "status": "success",
        }, response.status_code

    if 404 <= response.status_code <= 499 or 400 <= response.status_code <= 402:
        return {
            "stac_api_server_response": response.json(),
            "stac_api_server_response_code": response.status_code,
            "status": "failed"
        }, response.status_code
    else:
        return Response(response.text, response.status_code,
                        response.headers.items())


def get_items_by_collection_id(
        collection_id: str) -> Tuple[Dict[str, str], int] or Response:
    response = requests.get(route("COLLECTIONS") + collection_id + "/items")

    if response.status_code == 200:
        collection_json = response.json()
        return {
            "parameters": collection_json,
            "status": "success",
        }, response.status_code

    if 404 <= response.status_code <= 499 or 400 <= response.status_code <= 402:
        return {
            "stac_api_server_response": response.json(),
            "stac_api_server_response_code": response.status_code,
            "status": "failed"
        }, response.status_code
    else:
        return Response(response.text, response.status_code,
                        response.headers.items())


def get_item_from_collection(
        collection_id: str,
        item_id: str) -> Tuple[Dict[str, str], int] or Response:
    response = requests.get(
        route("COLLECTIONS") + collection_id + "/items/" + item_id)

    if response.status_code == 200:
        collection_json = response.json()
        return {
            "parameters": collection_json,
            "status": "success",
        }, response.status_code

    if 404 <= response.status_code <= 499 or 400 <= response.status_code <= 402:
        return {
            "stac_api_server_response": response.json(),
            "stac_api_server_response_code": response.status_code,
            "status": "failed"
        }, response.status_code
    else:
        return Response(response.text, response.status_code,
                        response.headers.items())
