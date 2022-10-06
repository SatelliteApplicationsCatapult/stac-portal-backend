import sqlalchemy
from flask import request
from flask_restx import Resource
from typing import Tuple, Dict
from ..util.dto import StacDto
api = StacDto.api
from ..service.stac_service import *
@api.route("/")
class CollectionsList(Resource):

    @api.doc(description="List all collections on the stac-api server")
    @api.response(200, "Success")
    @api.response(403, "Unauthorized")
    @api.response("4xx", "Stac API reported error")
    def get(self) -> Tuple[Dict[str, str], int]:
        return get_all_collections()

@api.route("/<collection_id>")
class Collection(Resource):

    @api.doc(description="get_collection")
    @api.response(200, "Success")
    @api.response(403, "Unauthorized")
    @api.response("4xx", "Stac API reported error")
    def get(self, collection_id: str) -> Tuple[Dict[str, str], int]:
        return get_collection_by_id(collection_id)

@api.route("/<collection_id>/items")
class CollectionItems(Resource):

    @api.doc(description="get_collection_items")
    @api.response(200, "Success")
    @api.response(403, "Unauthorized.")
    @api.response("4xx", "Stac API reported error")
    def get(self, collection_id: str) -> Tuple[Dict[str, str], int]:
        return get_items_by_collection_id(collection_id)
