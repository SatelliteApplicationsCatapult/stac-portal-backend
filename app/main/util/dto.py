from flask_restx import Namespace, fields


class UserDto:
    api = Namespace('user', description='user related operations')
    user = api.model(
        'user', {
            'email': fields.String(required=True,
                                   description='user email address'),
            'username': fields.String(required=True,
                                      description='user username'),
            'password': fields.String(required=True,
                                      description='user password'),
            'public_id': fields.String(description='user Identifier')
        })


class AuthDto:
    api = Namespace('auth', description='authentication related operations')
    user_auth = api.model(
        'auth_details', {
            'email':
            fields.String(required=True, description='The email address'),
            'password':
            fields.String(required=True, description='The user password '),
        })


class CollectionsDto:
    api = Namespace('collections', description='collection related operations')
    collection = api.model(
        'collections', {
            'collection_id':
            fields.String(required=True, description='collection status_id'),
            'item_id':
            fields.String(required=True, description='item status_id'),
        })


class ValidateDto:
    api = Namespace('validate', description='validate related operations')
    validate = api.model(
        'validate',
        {
            # takes a JSON object
            'json':
            fields.Raw(required=True, description='JSON object to validate'),
        })


class PublicCatalogsDto:
    api = Namespace('public_catalogs',
                    description='public catalogs related operations')
    add_public_catalog = api.model(
        "add_public_catalog", {
            'name':
            fields.String(required=True,
                          description='name of the public catalog'),
            'url':
            fields.String(required=True,
                          description='url of the public catalog'),
            'description':
            fields.String(required=True,
                          description='description of the public catalog'),
            'stac_version':
            fields.String(required=True,
                          description='STAC version of the public catalog'),
        })


class StacIngestionStatusDto:
    api = Namespace('stac_ingestion',
                    description='stac ingestion status related operations')
    stac_ingestion_status_get = api.model(
        'stac_ingestion', {
            'status_id':
            fields.String(required=False, description='status status_id'),
        })
    stac_ingestion_status_post = api.model(
        'stac_ingestion', {
            'newly_stored_collections_count':
            fields.Integer(required=True,
                           description='newly stored collections count'),
            'newly_stored_collections':
            fields.List(fields.String,
                        required=True,
                        description='newly stored collections'),
            'updated_collections_count':
            fields.Integer(required=True,
                           description='updated collections count'),
            'updated_collections':
            fields.List(fields.String,
                        required=True,
                        description='updated collections'),
            'newly_stored_items_count':
            fields.Integer(required=True,
                           description='newly stored items count'),
            'updated_items_count':
            fields.Integer(required=True, description='updated items count'),
            'already_stored_items_count':
            fields.Integer(required=True,
                           description='already stored items count'),
        }),
