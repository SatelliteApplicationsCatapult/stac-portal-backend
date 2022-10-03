from flask import request
from flask_restx import Resource
from werkzeug.utils import secure_filename

from ..service.file_service import *
from ..util.dto import FileDto

api = FileDto.api


@api.route("/blob_status")
class CheckBlobStatus(Resource):

    @api.doc(description="Check the status of a blob upload")
    @api.response(200, "Success")
    def get(self):
        available, message = check_blob_status()
        return {"available": available, "message": message}, 200


# @api.route("/stac_assets/<item_id>/stage")
# class UploadStacAssets(Resource):
#     @api.doc(description="Stage stac assets to the backend")
#     # @api.expect(FileDto.file_upload, validate=True)
#     @api.response(200, "Success")
#     def post(self, item_id):
#         try:
#             response = stage_file(item_id, request.files["filename"])
#             return {"message": response}, 200
#         except FileExistsError:
#             return {"message": "File already exists"}, 409


@api.route("/stac_assets/<item_id>/upload")
class CommitStacAssets(Resource):

    @api.doc(description="Upload stac assets to the azure storage blob")
    @api.response(200, "Success")
    @api.response(409, "Item already exists")
    @api.expect(FileDto.file_upload, validate=True)
    def post(self, item_id):
        args = FileDto.file_upload.parse_args()
        file = args["file"]
        filename = secure_filename(file.filename)
        if item_id not in filename:
            filename = f"{item_id}_{filename}"

        try:
            message = upload_filestream_to_blob(filename, file)
            return {"message": message}, 200
        except FileExistsError:
            return {"message": "File already exists"}, 409