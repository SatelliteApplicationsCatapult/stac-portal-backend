import os

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


@api.route("/stac_assets/upload")
class UploadStacAssets(Resource):
    @api.doc(description="Upload stac assets to blob storage")
    # @api.expect(FileDto.file_upload, validate=True)
    @api.response(200, "Success")
    def post(self):
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(filename)
        status, message = upload_file_to_blob(file)
        os.remove(filename)
        blob_path = "blob_path"
        return {"message": message, "filename": filename, "blob_path": blob_path}, 200
