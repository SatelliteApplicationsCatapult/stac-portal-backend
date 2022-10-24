from typing import Dict, Tuple

import requests
from flask import Response

from . import public_catalogs_service
from ..custom_exceptions import *
from ..model.public_catalogs_model import PublicCollection
from ..routes import route


def get_all_collections() -> dict[str, any]:
    response = requests.get(route("COLLECTIONS"))
    if response.status_code in range(200, 203):
        collection_json = response.json()
        # for each element in the collections array, check if it is public or private and add a new key
        public_collections: [] = public_catalogs_service.get_public_collections()
        public_collections_ids = [collection["id"] for collection in public_collections]
        for collection in collection_json["collections"]:
            # if collection id is in public collections, add its parent catalog id to the collection
            collection["management_metadata"] = {}
            if collection["id"] in public_collections_ids:
                # get the index of the collection in the public collections array
                index = public_collections_ids.index(collection["id"])
                collection["management_metadata"]["parent_catalog_id"] = public_collections[index]["parent_catalog"]
                collection["management_metadata"]["is_public"] = True
            else:
                collection["management_metadata"]["is_public"] = False
        return collection_json
        # return collection_json
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp


def get_collection_by_id(
        collection_id: str) -> dict[str, any]:
    response = requests.get(route("COLLECTIONS") + collection_id)
    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 404:
        raise CollectionDoesNotExistError
    elif response.status_code == 424:
        raise CollectionDoesNotExistError
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp


def get_items_by_collection_id(
        collection_id: str) -> dict[str, any]:
    response = requests.get(route("COLLECTIONS") + collection_id + "/items")

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 404:
        raise CollectionDoesNotExistError
    elif response.status_code == 424:
        raise CollectionDoesNotExistError
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp


def get_item_from_collection(
        collection_id: str,
        item_id: str) -> dict[str, any]:
    response = requests.get(
        route("COLLECTIONS") + collection_id + "/items/" + item_id)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 404:
        if "collection" in response.json()["description"].lower() and \
                "does not exist" in response.json()["description"].lower():
            raise CollectionDoesNotExistError
        elif "item" in response.json()["description"].lower() and \
                "does not exist" in response.json()["description"].lower():
            raise ItemDoesNotExistError
    elif response.status_code == 424:
        raise CollectionDoesNotExistError
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp


def create_new_collection_on_stac_api(
        collection_data: Dict[str,
                              any]) -> dict[str, any]:
    response = requests.post(route("COLLECTIONS"), json=collection_data)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 400:
        raise InvalidCollectionPayloadError
    elif response.status_code == 409:
        raise CollectionAlreadyExistsError
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp


def update_existing_collection_on_stac_api(
        collection_data: Dict[str,
                              any]) -> dict[str, any]:
    response = requests.put(route("COLLECTIONS"), json=collection_data)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 400:
        raise InvalidCollectionPayloadError
    elif response.status_code == 404:
        if "collection" in response.json()["description"].lower() \
                and "does not exist" in response.json()["description"].lower():
            raise CollectionAlreadyExistsError
        elif "item" in response.json()["description"].lower() \
                and "does not exist" in response.json()["description"].lower():
            raise ItemDoesNotExistError
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp


def remove_public_collection_by_id_on_stac_api(
        collection_id: str) -> Dict[any, any]:
    """Remove a collection by ID from the STAC API server.

    Additionally, removes all stored search parameters associated with the collection.


    :param collection_id: Collection ID to remove.
    :return: Either a tuple containing stac server response and status code, or a Response object.
    """
    response = requests.delete(route("COLLECTIONS") + collection_id)

    public_catalogs_service.remove_search_params_for_collection_id(
        collection_id)
    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 400:
        raise InvalidCollectionPayloadError
    elif response.status_code == 404:
        raise CollectionDoesNotExistError
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp


def remove_private_collection_by_id_on_stac_api(collection_id: str) -> Dict[str, any]:
    response = requests.delete(route("COLLECTIONS") + collection_id)
    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 400:
        raise InvalidCollectionPayloadError
    elif response.status_code == 404:
        raise PrivateCollectionDoesNotExistError
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp


def add_item_to_collection_on_stac_api(
        collection_id: str,
        item_data: Dict[str, any]) -> Dict[str, any]:
    response = requests.post(route("COLLECTIONS") + collection_id + "/items",
                             json=item_data)
    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 400:
        raise InvalidCollectionPayloadError
    elif response.status_code == 404:
        raise CollectionDoesNotExistError
    elif response.status_code == 409:
        raise ItemAlreadyExistsError
    elif response.status_code == 424:
        raise CollectionDoesNotExistError
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp


def update_item_in_collection_on_stac_api(
        collection_id: str, item_id: str,
        item_data: Dict[str, any]) -> Tuple[Dict[str, any], int] or Response:
    response = requests.put(route("COLLECTIONS") + collection_id + "/items/" +
                            item_id,
                            json=item_data)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 400:
        raise InvalidCollectionPayloadError
    elif response.status_code == 404:
        raise CollectionDoesNotExistError
    elif response.status_code == 424:
        raise CollectionDoesNotExistError
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp


def remove_item_from_collection_on_stac_api(
        collection_id: str,
        item_id: str) -> Tuple[Dict[str, any], int] or Response:
    response = requests.delete(
        route("COLLECTIONS") + collection_id + "/items/" + item_id)

    if response.status_code in range(200, 203):
        collection_json = response.json()
        return collection_json
    elif response.status_code == 400:
        raise InvalidCollectionPayloadError
    elif response.status_code == 404:
        raise CollectionDoesNotExistError
    elif response.status_code == 424:
        raise CollectionDoesNotExistError
    else:
        resp = response.json()
        resp["error_code"] = response.status_code
        return resp
