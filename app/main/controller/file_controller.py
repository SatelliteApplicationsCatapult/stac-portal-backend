from flask import request
from flask_restx import Resource
from werkzeug.utils import secure_filename

from ..service.file_service import *
from ..util.dto import FileDto, FilesDto

api = FileDto.api
files_api = FilesDto.files_api


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


@api.route("/stac_assets/<item_id>/url")
class RetrieveStacAssets(Resource):
    @api.doc(description="Retrieve stac assets from the backend")
    @api.response(200, "Success")
    @api.response(404, "Item not found")
    def get(self, item_id):
        try:
            file_url = return_file_url(item_id)
            response = retrieve_file(file_url)
            return {"message": response}, 200
        except FileNotFoundError:
            return {"message": "File not found"}, 404


# This takes multiple files and uploads them to the blob
@api.route("/stac_assets/upload")
class Upload(Resource):
    @files_api.doc(description="Upload stac assets to the azure storage blob")
    @files_api.response(200, "Success")
    @files_api.response(409, "Item already exists")
    @files_api.expect(FilesDto.files_upload, validate=True)
    def post(self):
        try:
            item_ids = request.form["itemIds"].split(",")
        except:
            return {"message": "No item ids provided"}, 400

        for i in range(len(item_ids)):
            item_id = item_ids[i]

            if item_id:
                file = request.files[f"file[{i}]"]
                filename = secure_filename(file.filename)
                if item_id not in filename:
                    filename = f"{item_id}_{filename}"
                try:
                    upload_filestream_to_blob(filename, file)
                except FileExistsError:
                    return {"message": "Success"}, 200
                except Exception as e:
                    # Log error
                    print(e)
                    return {"message": "Error uploading file"}, 400

        return {"message": "Success"}, 200
