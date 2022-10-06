from flask import request
from flask_restx import Resource

from ..custom_exceptions import *
from ..service import public_catalogs_service
from ..util.dto import PublicCatalogsDto

api = PublicCatalogsDto.api


@api.route('/')
class PublicCatalogs(Resource):

    @api.doc(description="""Get all public catalogs stored in the database.""")
    @api.doc('List all public catalogs in the database')
    @api.response(200, 'Success')
    def get(self):
        return public_catalogs_service.get_all_stored_public_catalogs_as_list_of_dict()

    @api.doc(description='Store a new public catalog in the database')
    @api.expect(PublicCatalogsDto.add_public_catalog, validate=True)
    @api.response(201, 'Success')
    @api.response(400, 'Validation Error - Some elements are missing')
    @api.response(409, 'Conflict - Catalog already exists')
    def post(self):
        try:
            data = request.json
            name = data['name']
            url = data['url']
            description = data['description']
            return public_catalogs_service.store_new_public_catalog(
                name, url, description), 201
        except IndexError as e:
            return {
                       'message': 'Some elements in json body are not present',
                   }, 400
        except CatalogAlreadyExistsError as e:
            return {
                       'message': 'Catalog with this url already exists',
                   }, 409

    @api.doc(description='Delete all public catalogs from the database')
    @api.response(200, 'Success')
    def delete(self):
        public_catalogs_service.remove_all_public_catalogs()
        return {"message": "Deleted all catalogs"}, 200


@api.route('/sync')
class PublicCatalogsUpdate(Resource):
    @api.doc(description='Get all public catalogs and update them')
    @api.response(200, 'Success')
    def get(self):
        return public_catalogs_service.store_publicly_available_catalogs(), 200


# @api.route("/<int:public_catalog_id>/collections")
# class PublicCatalogsCollections(Resource):
#     @api.doc(description='Get all collections of a public catalog')
#     @api.response(200, 'Success')
#     @api.response(404, 'Not Found - Catalog does not exist')
#     def get(self, public_catalog_id):
#         try:
#             return public_catalogs_service.get_all_available_collections_from_public_catalog_via_catalog_id(
#                 public_catalog_id), 200
#         except CatalogDoesNotExistError as e:
#             return {
#                        'message': 'Catalog with this id does not exist',
#                    }, 404


# @api.route("/collections")
# class PublicCatalogsCollections(Resource):
#     @api.doc(description='Get all collections of all public catalogs')
#     @api.response(200, 'Success')
#     def get(self):
#         return public_catalogs_service.get_all_available_collections_from_all_public_catalogs(), 200


@api.route('/<int:public_catalog_id>')
class PublicCatalogsViaId(Resource):

    @api.doc(description="""Get the details of a public catalog by its id.""")
    @api.response(200, 'Success')
    @api.response(404, 'Public catalog not found')
    def get(self, public_catalog_id):
        try:
            return public_catalogs_service.get_public_catalog_by_id_as_dict(
                public_catalog_id)

        except CatalogDoesNotExistError:
            return {'message': 'Public catalog not found'}, 404

    @api.doc(description='Remove a public catalog via its id')
    @api.response(200, 'Success')
    @api.response(404, 'Public catalog not found so it cant be removed')
    def delete(self, public_catalog_id):
        try:
            return public_catalogs_service.remove_public_catalog_via_catalog_id(
                public_catalog_id)
        except CatalogDoesNotExistError as e:
            return {'message': 'No result found'}, 404


@api.route('/<int:public_catalog_id>/items/get')
class GetStacRecordsSpecifyingPublicCatalogId(Resource):

    @api.doc(description="""Get specific collections from catalog.""")
    @api.expect(PublicCatalogsDto.start_stac_ingestion, validate=True)
    @api.response(200, 'Success')
    def post(self, public_catalog_id):
        data = request.json
        try:
            return public_catalogs_service.load_specific_collections_via_catalog_id(
                public_catalog_id, data), 200
        except CatalogDoesNotExistError as e:
            return {'message': 'Public catalog not found'}, 404
        except ConnectionError as e:
            return {
                       'message':
                           'Connection Error, ingestion microservice is probably down'
                   }, 500


@api.route('/items/update')
class UpdateAllStacRecords(Resource):

    @api.doc(
        description='Update all stored stac records from all public catalogs')
    def get(self):
        try:
            result = public_catalogs_service.update_all_stac_records()
            response = []
            for i in result:
                response.append({
                    "operation_number": i,
                })
            return response, 200
        except ConnectionError as e:
            return {
                       'message':
                           'Connection Error, ingestion microservice is probably down'
                   }, 500


@api.route('/<int:public_catalog_id>/items/update')
class UpdateStacRecordsSpecifyingPublicCatalogId(Resource):

    @api.doc(description="""Get all stac records from a public catalog.""")
    @api.response(200, 'Success')
    @api.response(404, 'Public catalog not found')
    def get(self, public_catalog_id):
        try:
            return public_catalogs_service.update_specific_collections_via_catalog_id(
                public_catalog_id)
        except CatalogDoesNotExistError:
            return {'message': 'Public catalog not found'}, 404
        except ConnectionError as e:
            return {
                       'message':
                           'Connection Error, ingestion microservice is probably down'
                   }, 500

    @api.doc(description="""Update specific collections from catalog.""")
    @api.expect(
        PublicCatalogsDto.update_stac_collections_specify_collection_ids,
        validate=True)
    @api.response(200, 'Success')
    def post(self, public_catalog_id):
        collections_to_update = request.json['collections']
        try:
            result = public_catalogs_service.update_specific_collections_via_catalog_id(
                public_catalog_id, collections_to_update)
            response = []
            for i in result:
                response.append({
                    "message": i,
                })
            return response, 200
        except CatalogDoesNotExistError as e:
            return {
                       'message': 'Public catalog with specified id not found'
                   }, 404
        except ConnectionError as e:
            return {
                       'message':
                           'Connection Error, ingestion microservice is probably down'
                   }, 500
