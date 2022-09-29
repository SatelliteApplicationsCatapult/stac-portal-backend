#!/usr/bin/python
# -*- coding: utf-8 -*-
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
            'public_id': fields.String(description='user Identifier'),
        })


class AuthDto:

    api = Namespace('auth', description='authentication related operations')
    user_auth = api.model(
        'auth_details', {
            'email':
            fields.String(required=True, description='The email address'),
            'password':
            fields.String(required=True, description='The user password ')
        })


class CollectionsDto:

    api = Namespace('collections', description='collection related operations')
    collection = api.model(
        'collections', {
            'collection_id':
            fields.String(required=True, description='collection status_id'),
            'item_id':
            fields.String(required=True, description='item status_id')
        })
    collection_dto = api.model('collection_dto', {  # TODO: Check: Follow collection spec fully, recurse it all the way down
                                                    # Must follow https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md
        'type': fields.String(required=True,
                              description='Collection type',
                              example='Collection'),
        'stac_version': fields.String(required=True,
                description='stac version', example='1.0.0'),
        'id': fields.String(required=True, description='collection id',
                            example='custom-landsat-c2-l2'),
        'description': fields.String(required=True,
                description='collection description',
                example='Custom Landsat Collection 2 Level 2'),
        'license': fields.String(required=True,
                                 description='collection license',
                                 example='proprietary'),
        'extent': fields.Nested(api.model('extent',
                                {'spatial': fields.List(fields.Float,
                                required=True,
                                description='spatial extent',
                                example=[-180, -90, 180, 90]),
                                'temporal': fields.List(fields.String,
                                required=True,
                                description='temporal extent',
                                example=['2021-05-05T00:00:00Z/2022-05-05T00:00:00Z'
                                ])}), required=True,
                                description='spatial and temporal extent'
                                ),
        })
    item_dto = api.model('item_dto', {  # TODO: Check: Follow collection spec fully, recurse it all the way down
                                        # Must follow https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md
        'type': fields.String(required=True, description='Item type',
                              example='Feature'),
        'stac_version': fields.String(required=True,
                description='stac version', example='1.0.0'),
        'id': fields.String(required=True, description='item id',
                            example='LC08_L2SP_20210505_20210505_02_RT'
                            ),
        'bbox': fields.List(fields.Float, required=False,
                            description='bbox', example=[-180, -90,
                            180, 90]),
        'geometry': fields.Nested(api.model('geometry',
                                  {'type': fields.String(required=True,
                                  description='geometry type',
                                  example='Polygon'),
                                  'coordinates': fields.List(fields.List(fields.List(fields.Float)),
                                  required=True,
                                  description='geometry coordinates',
                                  example=[[[-180, -90], [-180, 90],
                                  [180, 90], [180, -90], [-180,
                                  -90]]])}), required=False,
                                  description='geometry'),
        'properties': fields.Nested(api.model('properties',
                                    {'datetime': fields.String(required=True,
                                    description='datetime',
                                    example='2021-05-05T00:00:00Z')}),
                                    required=True),
        })


class ValidateDto:

    api = Namespace('validate', description='validate related operations')
    validate = api.model('validate', {
        'json':
        fields.Raw(required=True, description='JSON object to validate')
    })  # takes a JSON object


class PublicCatalogsDto:

    api = Namespace('public_catalogs',
                    description='public catalogs related operations')
    add_public_catalog = api.model(
        'add_public_catalog', {
            'name':
            fields.String(required=True,
                          description='name of the public catalog',
                          example='Microsoft Planetary Computer'),
            'url':
            fields.String(
                required=True,
                description='url of the public catalog',
                example='https://planetarycomputer.microsoft.com/api/stac/v1'),
            'description':
            fields.String(
                required=True,
                description='description of the public catalog',
                example=
                'The Planetary Computer is a cloud-based platform for planetary-scale geospatial data processing and analysis.'
            ),
            'stac_version':
            fields.String(required=True,
                          description='STAC version of the public catalog',
                          example='1.0.0'),
        })

    start_stac_ingestion = api.model('start_stac_ingestion', {  # 'source_stac_catalog_url':
                                                                # fields.String(
                                                                #     required=True,
                                                                #     description='url of the source STAC catalog',
                                                                #     example="https://planetarycomputer.microsoft.com/api/stac/v1"),
                                                                # 'target_stac_catalog_url':
                                                                # fields.String(required=True,
                                                                #               description='url of the destination STAC catalog',
                                                                #               example="https://stac-api-server.azurewebsites.net"),
        'update': fields.Boolean(required=True,
                                 description='update the destination catalog'
                                 ),
        'bbox': fields.List(fields.Float, required=False,
                            description='bounding box of the area to be ingested'
                            , example=[-1, 50, 1, 51]),
        'datetime': fields.String(required=False,
                                  description='datetime of the area to be ingested'
                                  ,
                                  example='2021-05-05T00:00:00Z/2022-05-05T00:00:00Z'
                                  ),
        'collections': fields.List(fields.String, required=False,
                                   description='collections to be ingested'
                                   , example=['landsat-8-l1-c1',
                                   'sentinel-2-l1c', 'landsat-c2-l2']),
        # 'intersects': fields.String(required=False,
        #                             description='geojson of the area to be ingested'
        #                             , example='{}'),
        # 'ids': fields.List(fields.String, required=False,
        #                    description='ids of the items to be ingested'
        #                    , example=[]),
        })
    update_stac_collections_specify_collection_ids = \
        api.model('update_stac_collections_specify_collection_ids',
                  {'collections': fields.List(fields.String,
                  required=True, default=[], example=['landsat-8-l1-c1'
                  , 'sentinel-2-l1c', 'landsat-c2-l2'])})
    update_stac_collections_via_catalog_url = \
        api.model('update_stac_collections_via_catalog_url',
                  {'source_catalog_url': fields.String(required=True,
                  description='Url of the source catalog in the database'
                  ,
                  example='https://planetarycomputer.microsoft.com/api/stac/v1'
                  ), 'collections': fields.List(fields.String,
                  required=False, default=[], example=['landsat-8-l1-c1'
                  , 'sentinel-2-l1c', 'landsat-c2-l2'])})


class StatusReportingDto:

    api = Namespace('status_reporting',
                    description='Status reporting related operations')
    stac_ingestion_status_post = api.model(
        'stac_ingestion_status_post', {
            'newly_stored_collections_count':
            fields.Integer(required=True,
                           description='number of newly stored collections'),
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
        })



class FileDto:

    api = Namespace('files', description='File upload related operations')
    file_upload = api.model('file_upload', {
        'file':
        fields.Raw(required=True, description='filename to upload')
    })  # takes a filename

class UploadDto:

    api = Namespace('upload', description='upload related operations')
    upload = api.model('upload', {
        'file':
        fields.Raw(required=True, description='files to upload')
    })  # takes a file
