from flask import request, jsonify
from flask_restx import Resource

from ..service.validate_service import validate_json
from ..util.dto import UploadDto
from typing import Dict, Tuple, Any

api = UploadDto.api
upload = UploadDto.upload


@api.route("/file")
class Uploader(Resource):
    """Validate JSON Resource."""

    @api.doc("Upload file")
    @api.expect(upload)
    def post(self) -> Tuple[Dict[str, str], int]:
        files = request.files
        for file in files:
            print("Received ::", files[file].filename)
        return "Success", 200
