from typing import Dict, Tuple

from flask import request, jsonify, Response
from flask_restx import Resource

from ..service.validate_service import validate_json
from ..util.dto import ValidateDto

api = ValidateDto.api
validate = ValidateDto.validate


@api.route("/json/")
class ValidateJSON(Resource):
    """Validate JSON Resource."""

    @api.doc("validate_json")
    @api.expect(validate)
    def post(self) -> Response:
        """Validate JSON."""
        data = request.json
        return jsonify(validate_json(data=data))
