from flask_restx import Resource
from ..service.file_upload_service import *
from ..util.dto import FileUploadDto
from flask_restx import Resource

from ..service.file_upload_service import *
from ..util.dto import FileUploadDto

api = FileUploadDto.api


@api.route("/blob_status")
class CheckBlobStatus(Resource):
    @api.doc(description="Check the status of a blob upload")
    @api.response(200, "Success")
    @api.response(403, "Unauthorized")
    @api.response("4xx", "Stac API reported error")
    def get(self) -> Tuple[Dict[str, str], int]:
        available, message = check_blob_status()
        return {"available": available, "message": message}, 200

