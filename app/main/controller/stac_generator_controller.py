from flask import request
from flask_restx import Resource

from ..util.dto import StacGeneratorDto
from ..service.stac_generator_service import create_STAC_Item


api = StacGeneratorDto.api

@api.route("/")
class StacGenerator(Resource):

    @api.doc(description="Generate STAC from tiffs and metadata")
    @api.expect(StacGeneratorDto.stac_generator, validate=False)
    @api.response(200, "Success")
    @api.response(404, "File not found")
    @api.response(500, "Internal server error")
    def post(self):
        data = request.json
        return create_STAC_Item(data)