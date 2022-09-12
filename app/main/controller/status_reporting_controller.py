import sqlalchemy
from flask import request
from flask_restx import Resource

from ..service import status_reporting_service
from ..util.dto import StatusReportingDto

api = StatusReportingDto.api


@api.route('/loading_public_stac_records')
class StacIngestionStatus(Resource):

    @api.doc(description='Get all statuses of stac ingestion statuses')
    def get(self):
        return status_reporting_service.get_all_stac_ingestion_statuses()


@api.route('/loading_public_stac_records/<string:status_id>')
class StacIngestionStatusViaId(Resource):

    @api.doc(description='get a stac ingestion status via status_id')
    def get(self, status_id):
        try:
            return status_reporting_service.get_stac_ingestion_status_by_id(
                status_id), 200
        except AttributeError:
            return {'message': 'No result found'}, 404

    @api.doc(
        description='Save a stac ingestion status with specified status_id')
    @api.expect(StatusReportingDto.stac_ingestion_status_post, validate=True)
    def post(self, status_id):
        request_data = request.get_json()
        print(request_data)
        newly_stored_collections_count = request_data[
            'newly_stored_collections_count']
        newly_stored_collections = request_data['newly_stored_collections']
        updated_collections_count = request_data['updated_collections_count']
        updated_collections = request_data['updated_collections']
        print(updated_collections)
        newly_stored_items_count = request_data['newly_stored_items_count']
        updated_items_count = request_data['updated_items_count']
        already_stored_items_count = request_data['already_stored_items_count']
        try:
            response = status_reporting_service.set_stac_ingestion_status_entry(
                status_id, newly_stored_collections_count,
                newly_stored_collections, updated_collections_count,
                updated_collections, newly_stored_items_count,
                updated_items_count, already_stored_items_count)

            return response, 201
        except AttributeError as e:
            return {'message': 'No status with specified id to update'}, 404

    @api.doc(
        description='Delete a stac ingestion status with specified status_id')
    def delete(self, status_id):
        try:
            return status_reporting_service.remove_stac_ingestion_status_entry(
                status_id), 200
        except sqlalchemy.orm.exc.UnmappedInstanceError as e:
            return {'message': 'No result found to delete'}, 404
