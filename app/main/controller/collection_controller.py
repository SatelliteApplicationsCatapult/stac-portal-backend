from flask import request
from flask_restx import Resource

from ..service.collection_service import *
from ..util.dto import CollectionsDto

api = CollectionsDto.api
collections = CollectionsDto.collection


@api.route("/")
class CollectionsList(Resource):
    """Collections Resource."""

    @api.doc("List all collections on the stac-api server")
    @api.response(200, "Success")
    @api.response(403, "Unauthorized")
    @api.response("4xx", "Stac API reported error")
    def get(self) -> Tuple[Dict[str, str], int]:
        return get_all_collections()

    @api.doc("Create a new collection on the stac-api server")
    @api.expect(CollectionsDto.collection_dto, validate=True)
    @api.response(200, "Success")
    @api.response(403, "Unauthorized")
    @api.response("4xx", "Stac API reported error")
    def post(self):
        return create_new_collection(request.json)

    @api.doc("Update a collection on the stac-api server")
    @api.expect(CollectionsDto.collection_dto, validate=True)
    @api.response(200, "Success")
    @api.response(403, "Unauthorized")
    @api.response("4xx", "Stac API reported error")
    def put(self) -> Tuple[Dict[str, str], int]:
        return update_existing_collection(request.json)


@api.route("/<collection_id>")
class Collection(Resource):
    """Collection Resource."""

    @api.doc("get_collection")
    @api.response(200, "Success")
    @api.response(403, "Unauthorized")
    @api.response("4xx", "Stac API reported error")
    def get(self, collection_id: str) -> Tuple[Dict[str, str], int]:
        return get_collection_by_id(collection_id)

    @api.doc("Remove collection by id")
    @api.response(200, "Collection removed successfully.")
    @api.response(403, "Unauthorized.")
    @api.response("4xx", "Stac API reported error")
    def delete(self, collection_id: str) -> Tuple[Dict[str, str], int]:
        return remove_collection_by_id(collection_id)


@api.route("/<collection_id>/items")
class CollectionItems(Resource):

    @api.doc("get_collection_items")
    def get(self, collection_id: str) -> Tuple[Dict[str, str], int]:
        return get_items_by_collection_id(collection_id)

    @api.doc("Add item to collection")
    @api.expect(CollectionsDto.item_dto, validate=True)
    def post(self, collection_id):
        return add_item_to_collection(collection_id, request.json)


@api.route("/<collection_id>/items/<item_id>")
class CollectionItem(Resource):
    """Collection Item Resource."""

    @api.doc("get_collection_item")
    def get(self, collection_id: str,
            item_id: str) -> Tuple[Dict[str, str], int]:
        return get_item_from_collection(collection_id, item_id)

    def put(self):
        raise NotImplemented

    def delete(self):
        raise NotImplemented
