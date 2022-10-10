from typing import Tuple

from flask import request
from flask_restx import Resource

from ..custom_exceptions import *
from ..service.private_catalog_service import *
from ..service.stac_service import *
from ..util.dto import CollectionsDto

api = CollectionsDto.api
collections = CollectionsDto.collection


@api.route("/collections")
class CollectionsList(Resource):
    @api.doc(description="Create a new private collection")
    @api.expect(CollectionsDto.collection_dto, validate=True)
    @api.response(200, "Success")
    @api.response(400, "Validation Error")
    @api.response(403, "Unauthorized")
    @api.response("4xx", "Stac API reported error")
    def post(self):
        try:
            return add_collection(request.json)
        except PrivateCollectionAlreadyExistsError as e:
            return {
                       "message": "Collection with this ID already exists",
                   }, 409
        except ConvertingTimestampError as e:
            return {
                       "message": f"Error converting timestamp: {e}",
                   }, 400

    @api.doc(description="Update a private collection")
    @api.expect(CollectionsDto.collection_dto, validate=True)
    @api.response(200, "Success")
    @api.response(400, "Validation Error")
    @api.response(404, "Collection not found")
    @api.response("4xx", "Stac API reported error")
    def put(self):
        try:
            return update_collection(request.json), 200
        except PrivateCollectionDoesNotExistError as e:
            return {
                       "message": "Collection with this ID not found",
                   }, 404
        except ConvertingTimestampError as e:
            return {
                       "message": f"Error converting timestamp: {e}",
                   }, 400


@api.route("/collections/<collection_id>")
class Collection(Resource):
    @api.doc(description="Remove private collection by id")
    @api.response(200, "Collection removed successfully.")
    @api.response(404, "Collection not found")
    def delete(self, collection_id: str) -> Tuple[Dict[str, str], int]:
        try:
            return remove_collection(collection_id), 200
        except PrivateCollectionDoesNotExistError as e:
            return {
                       "message": "Collection with this ID not found",
                   }, 404


@api.route("/collections/<collection_id>/items")
class CollectionItems(Resource):

    @api.doc(description="Add item to private collection")
    @api.response(200, "Success")
    @api.response(403, "Unauthorized.")
    @api.response("4xx", "Stac API reported error")
    @api.expect(CollectionsDto.item_dto, validate=True)
    def post(self, collection_id):
        try:
            return add_item_to_collection_on_stac_api(collection_id, request.json)
        except CollectionDoesNotExistError as e:
            return {
                       "message": "Collection with this ID not found",
                   }, 404
        except ItemAlreadyExistsError as e:
            return {
                       "message": "Item with this ID already exists",
                   }, 409
        except ConvertingTimestampError as e:
            return {
                       "message": f"Error converting timestamp: {e}",
                   }, 400


@api.route("/collections/<collection_id>/items/<item_id>")
class CollectionItem(Resource):

    @api.doc(description="Update item in private collection")
    @api.response(200, "Success")
    @api.response(403, "Unauthorized.")
    @api.expect(CollectionsDto.item_dto, validate=True)
    def put(self, collection_id: str, item_id: str):
        try:
            return update_item_in_collection_on_stac_api(collection_id, item_id, request.json), 200
        except CollectionDoesNotExistError as e:
            return {
                       "message": "Collection with this ID not found",
                   }, 404
        except ItemDoesNotExistError as e:
            return {
                       "message": "Item with this ID not found",
                   }, 404

    @api.doc(description="Remove item from private collection")
    @api.response(200, "Success")
    @api.response(403, "Unauthorized.")
    @api.response("4xx", "Stac API reported error")
    def delete(self, collection_id: str, item_id: str):
        try:
            return remove_item_from_collection_on_stac_api(collection_id, item_id),200
        except CollectionDoesNotExistError as e:
            return {
                       "message": "Collection with this ID not found",
                   }, 404
        except ItemDoesNotExistError as e:
            return {
                       "message": "Item with this ID not found",
                   }, 404

