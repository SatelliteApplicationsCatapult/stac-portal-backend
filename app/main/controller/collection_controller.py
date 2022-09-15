from typing import Dict, Tuple

from flask_restx import Resource

from ..service.collection_service import *
from ..util.dto import CollectionsDto

api = CollectionsDto.api
collections = CollectionsDto.collection


@api.route("/")
class CollectionsList(Resource):
    """Collections Resource."""

    @api.doc("list_of_collections")
    def get(self) -> Tuple[Dict[str, str], int]:
        """List all collections."""
        return get_all_collections()


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
    """Collection Items Resource."""

    @api.doc("get_collection_items")
    def get(self, collection_id: str) -> Tuple[Dict[str, str], int]:
        """Get a collection by status_id."""
        return get_items_by_collection_id(collection_id)


@api.route("/<collection_id>/items/<item_id>")
class CollectionItem(Resource):
    """Collection Item Resource."""

    @api.doc("get_collection_item")
    def get(self, collection_id: str,
            item_id: str) -> Tuple[Dict[str, str], int]:
        """Get a collection by status_id."""
        return get_item_from_collection(collection_id, item_id)
