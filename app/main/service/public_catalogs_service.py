import datetime
import json
from threading import Thread
from typing import Dict, List

import geoalchemy2
import requests
import sqlalchemy
from flask import current_app
from shapely.geometry import box
from shapely.geometry import MultiPolygon, Polygon

from app.main.model.public_catalogs_model import PublicCatalog, PublicCollection
from .status_reporting_service import make_stac_ingestion_status_entry, set_stac_ingestion_status_entry
from .. import db
from ..custom_exceptions import *
from ..model.public_catalogs_model import StoredSearchParameters


def store_new_public_catalog(name: str, url: str, description: str) -> Dict[any, any]:
    """Store a new public catalog in the database.

    :param name: Name of the catalog
    :param url: URL of the catalog, to stac api root
    :param description: Description of the catalog
    :param stac_version: Stac version catalogue used
    :return: New catalogue parameters from database as dict
    """
    try:
        a: PublicCatalog = PublicCatalog()
        a.name = name
        a.url = url
        a.description = description
        db.session.add(a)
        db.session.commit()
        return a.as_dict()
    except sqlalchemy.exc.IntegrityError:
        # rollback the session
        db.session.rollback()
        raise CatalogAlreadyExistsError


def get_publicly_available_catalogs() -> List[Dict[any, any]]:
    lookup_api: str = "https://stacindex.org/api/catalogs"
    response = requests.get(lookup_api)
    response_result = response.json()
    filtered_response_result = [i for i in response_result if i['isPrivate'] == False and i['isApi'] == True]
    return _store_publicly_available_catalogs(filtered_response_result)


def remove_all_catalogs():
    """Remove all catalogs from the database."""
    db.session.query(PublicCatalog).delete()
    db.session.commit()


def _store_catalog(title, url, summary):
    try:
        url_removed_slash = url[:-1] if url.endswith('/') else url
        response = requests.get(url_removed_slash + '/collections')
        # if response is not 200, skip this catalog
        if response.status_code != 200:
            print("Skipping not-public catalog: " + title)
            return None
        response_2 = requests.get(url_removed_slash + '/search?limit=1')
        if response_2.status_code != 200:
            print("Skipping not-public catalog: " + title)
            return None
        if len(response_2.json()['features']) != 1:
            print("Skipping not-public catalog: " + title)
            return None
        new_catalog = store_new_public_catalog(title, url, summary)
        new_catalog_id = new_catalog['id']
        collections_for_new_catalog: List[
            Dict[any, any]] = get_all_available_collections_from_public_catalog_via_catalog_id(new_catalog_id)
        # for each new collection, store it in the database
        for collection in collections_for_new_catalog:
            public_collection: PublicCollection = PublicCollection()
            public_collection.id = collection['id']
            try:
                public_collection.type = collection['type']
            except KeyError:
                public_collection.type = "Collection"
            public_collection.title = collection['title']
            public_collection.description = collection['description']
            start_time_string = collection['extent']['temporal']['interval'][0][0]
            end_time_string = collection['extent']['temporal']['interval'][0][1]
            potential_datetime_formats = ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%dT%H:%M:%S.%f']
            if start_time_string is not None:
                public_collection.start_time = None
                for fmt in potential_datetime_formats:
                    try:
                        public_collection.start_time = datetime.datetime.strptime(start_time_string, fmt)
                        break
                    except ValueError:
                        continue
                if public_collection.start_time is None:
                    raise ConvertingTimestampError
            if end_time_string is not None:
                public_collection.end_time = None
                for fmt in potential_datetime_formats:
                    try:
                        public_collection.end_time = datetime.datetime.strptime(end_time_string, fmt)
                        break
                    except ValueError:
                        continue
                if public_collection.end_time is None:
                    raise ConvertingTimestampError
            bboxes = collection['extent']['spatial']['bbox']
            shapely_boxes = []
            for i in range(0, len(bboxes)):
                shapely_box = box(*(collection['extent']['spatial']['bbox'][i]))
                shapely_boxes.append(shapely_box)
            shapely_multi_polygon = geoalchemy2.shape.from_shape(MultiPolygon(shapely_boxes))
            public_collection.spatial_extent = shapely_multi_polygon
            public_collection.parent_catalog = new_catalog_id  # TODO: Rename to parent_catalog_id
            db.session.add(public_collection)
            db.session.commit()
        return new_catalog
    except CatalogAlreadyExistsError:
        pass
    except ConvertingTimestampError:
        print("Could not convert timestamp")
    except (KeyError) as e:
        # print the error
        print("Url of problem catalog: " + url)
        print(e)
        # remove new_catalog from database via url
        db.session.query(PublicCatalog).filter_by(url=url).delete()
        db.session.commit()
    return None


def _store_publicly_available_catalogs(catalogs: List[Dict[any, any]]):
    """Store all publicly available catalogs in the database.

    :param catalogs: List of catalogs as dicts
    """
    results = []
    for catalog in catalogs:
        results.append((_store_catalog(
            catalog['title'], catalog['url'], catalog['summary'])))
    return [i for i in results if i is not None]


def get_all_available_collections_from_public_catalog_via_catalog_id(public_catalog_id: int) -> List[Dict[any, any]]:
    """Get all collections from a catalog specified by its id."""
    try:
        a: PublicCatalog = PublicCatalog.query.filter_by(
            id=public_catalog_id).first()
        return get_all_available_collections_from_public_catalog(a)
    except AttributeError:
        raise CatalogDoesNotExistError


def get_all_available_collections_from_public_catalog(public_catalogue_entry: PublicCatalog) -> List[Dict[
    any, any]] or None:
    """Get all collections from a catalog specified by its id."""
    print("Doing catalog: " + public_catalogue_entry.name)
    try:
        if public_catalogue_entry is None:
            return None
        url = public_catalogue_entry.url
        # if url ends with /, remove it
        if url.endswith('/'):
            url = url[:-1]
        collections_url = url + '/collections'
        response = requests.get(collections_url)
        response_result = response.json()
        return response_result['collections']
    except:
        print("Url of problem catalog: " + public_catalogue_entry.url)


def get_all_available_collections_from_all_public_catalogs() -> List[List[Dict[any, any]]]:
    """Get all collections from all public catalogs."""
    data = []
    public_catalogs: [PublicCatalog] = PublicCatalog.query.all()
    for public_catalog in public_catalogs:
        data.append ((get_all_available_collections_from_public_catalog(public_catalog)))
    # return data where not None
    return [i for i in data if i is not None]


def get_all_available_collections_from_all_public_catalogs_filter_via_polygon(polygons) -> List[str]:
    pass


def get_all_stored_public_catalogs_as_list_of_dict() -> List[Dict[any, any]]:
    """Get all public catalogs from the database.

    :return: List of all public catalogs as list of dicts
    """
    a: [PublicCatalog] = PublicCatalog.query.all()
    return [i.as_dict() for i in a]


def get_public_catalog_by_id_as_dict(public_catalog_id: int) -> Dict[any, any]:
    """Get a public catalog by its id.

    :param public_catalog_id: Id of the public catalog
    :return: Public catalog as dict
    """
    try:
        a: PublicCatalog = PublicCatalog.query.filter_by(
            id=public_catalog_id).first()
        return a.as_dict()
    except AttributeError:
        raise CatalogDoesNotExistError


def remove_public_catalog_via_catalog_id(public_catalog_id: int) -> Dict[any, any]:
    """Remove a public catalog by its id.

    :param public_catalog_id: Id of the public catalog
    :return: Public catalog as dict
    """
    try:
        a: PublicCatalog = PublicCatalog.query.filter_by(
            id=public_catalog_id).first()
        db.session.delete(a)
        db.session.commit()
        return a.as_dict()
    except sqlalchemy.orm.exc.UnmappedInstanceError as e:
        raise CatalogDoesNotExistError


def load_get_specific_collections_via_catalog_id(catalog_id: int,
                                                 parameters: Dict[any, any] = None):
    """Get all collections from a catalog specified by its id.

    The search query will be added to the database so the inserted records
    can easily be updated later on by forcing update flag to True

    :param catalog_id: Id of the catalog
    :param parameters: Parameters for the search from stac item-search standard

    :return: Response from the ingestion microservice
    """
    public_catalogue_entry: PublicCatalog = PublicCatalog.query.filter_by(
        id=catalog_id).first()
    if public_catalogue_entry is None:
        raise CatalogDoesNotExistError("No catalogue entry found for id: " +
                                       str(catalog_id))
    if parameters is None:
        parameters = {}
    parameters['source_stac_catalog_url'] = public_catalogue_entry.url
    target_stac_api_url = current_app.config['TARGET_STAC_API_SERVER']
    _store_search_parameters(catalog_id, parameters)
    parameters["target_stac_catalog_url"] = target_stac_api_url
    # result = q.enqueue(_call_ingestion_microservice, parameters)
    # return result.id
    return _call_ingestion_microservice(parameters)


def update_all_stac_records() -> list[int]:
    """Run the search using every stored search parameter.

    :return: List of tuples containing the responses from the selective ingester microservice and the work id
    """
    stored_search_parameters: [StoredSearchParameters
                               ] = StoredSearchParameters.query.all()
    return _run_ingestion_task_force_update(stored_search_parameters)


def update_specific_collections_via_catalog_id(catalog_id: int,
                                               collections: [str] = None
                                               ) -> list[int]:
    """Get all stored search parameters for a specific catalogue id. Then
    combine them all together and pass on for update.

    :param catalog_id: Catalogue id to update it's collections
    :param collections: Specific collections to update. If None, all collections will be updated
    :return: List of tuples containing the responses from the selective ingester microservice and the work id
    """
    print("Updating collections for catalogue id: " + str(catalog_id))
    public_catalogue_entry: PublicCatalog = PublicCatalog.query.filter_by(
        id=catalog_id).first()

    if public_catalogue_entry is None:
        raise CatalogDoesNotExistError("No catalogue entry found for id: " +
                                       str(catalog_id))
    print("Public catalogue entry: " + str(public_catalogue_entry))
    stored_search_parameters: [StoredSearchParameters
                               ] = StoredSearchParameters.query.filter_by(
        associated_catalog_id=catalog_id).all()
    print("Stored search parameters: " + str(stored_search_parameters))
    stored_search_parameters_to_run = []
    if collections is None or len(collections) == 0:
        stored_search_parameters_to_run = stored_search_parameters
        return _run_ingestion_task_force_update(
            stored_search_parameters_to_run)
    else:
        for stored_search_parameter in stored_search_parameters:
            used_search_parameters = json.loads(
                stored_search_parameter.used_search_parameters)
            used_search_parameters_collections = used_search_parameters[
                'collections']
            # if any collection in used_search_parameters_collections is in collections, then add to stored_search_parameters_to_run
            check = any(item in used_search_parameters_collections
                        for item in collections)
            if check:
                stored_search_parameters_to_run.append(stored_search_parameter)

        return _run_ingestion_task_force_update(
            stored_search_parameters_to_run)


def _call_ingestion_microservice(parameters) -> int:
    souce_stac_catalog_url = parameters['source_stac_catalog_url']
    target_stac_catalog_url = current_app.config['TARGET_STAC_API_SERVER']
    update = parameters['update']
    callback_id = make_stac_ingestion_status_entry(souce_stac_catalog_url, target_stac_catalog_url, update)
    parameters['callback_id'] = callback_id
    microservice_endpoint = current_app.config['STAC_SELECTIVE_INGESTER_ENDPOINT']

    def run_async(_parameters, _app):
        try:
            print("Microservice endpoint: " + microservice_endpoint)
            response = requests.post(
                microservice_endpoint,
                json=_parameters, timeout=None)
            # convert response to json
            response_json = response.json()
            newly_stored_collections = response_json['newly_stored_collections']
            newly_stored_collections_count = response_json['newly_stored_collections_count']
            updated_collections_count = response_json['updated_collections_count']
            updated_collections = response_json['updated_collections']
            newly_stored_items_count = response_json['newly_stored_items_count']
            updated_items_count = response_json['updated_items_count']
            already_stored_items_count = response_json['already_stored_items_count']
            with _app.app_context():
                set_stac_ingestion_status_entry(int(callback_id), newly_stored_collections_count,
                                                newly_stored_collections,
                                                updated_collections_count, updated_collections,
                                                newly_stored_items_count,
                                                updated_items_count, already_stored_items_count)
            return response_json

        except Exception as e:
            print("Error: " + str(e))
            raise ConnectionError("Could not connect to stac selective ingester microservice")

    app = current_app._get_current_object()  # TODO: Is there a better way to do this?
    thread = Thread(target=run_async, args=(parameters, app))
    thread.start()
    return callback_id


def _store_search_parameters(associated_catalogue_id,
                             parameters: dict) -> None:
    """Store the search parameters in the database so they can be used to
    update the data later on.

    Separate each collection into it's own search parameter so they can be updated individually with ease.

    :param associated_catalogue_id:
    :param parameters:
    :return:
    """
    try:
        for collection in parameters['collections']:
            filtered_parameters = parameters.copy()
            filtered_parameters['collections'] = [collection]

            try:
                stored_search_parameters = StoredSearchParameters()
                stored_search_parameters.associated_catalog_id = associated_catalogue_id
                stored_search_parameters.used_search_parameters = json.dumps(
                    filtered_parameters)
                stored_search_parameters.collection = collection
                try:
                    stored_search_parameters.bbox = json.dumps(
                        filtered_parameters['bbox'])
                except KeyError:
                    pass
                try:
                    stored_search_parameters.datetime = json.dumps(
                        filtered_parameters['datetime'])
                except KeyError:
                    pass

                db.session.add(stored_search_parameters)
                db.session.commit()
                return
            except sqlalchemy.exc.IntegrityError:
                # exact same search parameters already exist, no need to store them again
                pass
            finally:
                db.session.rollback()
    except KeyError:
        filtered_parameters = parameters.copy()
        try:
            stored_search_parameters = StoredSearchParameters()
            stored_search_parameters.associated_catalog_id = associated_catalogue_id
            stored_search_parameters.used_search_parameters = json.dumps(
                filtered_parameters)
            try:
                stored_search_parameters.bbox = json.dumps(
                    filtered_parameters['bbox'])
            except KeyError:
                pass
            try:
                stored_search_parameters.datetime = json.dumps(
                    filtered_parameters['datetime'])
            except KeyError:
                pass

            db.session.add(stored_search_parameters)
            db.session.commit()
            return
        except sqlalchemy.exc.IntegrityError:
            # exact same search parameters already exist, no need to store them again
            pass
        finally:
            db.session.rollback()


def remove_search_params_for_collection_id(collection_id: str) -> int:
    """Remove all stored search parameters for a given collection id.

    :param collection_id: The collection id to remove
    :return: The number of search parameters removed
    """
    num_deleted = 0
    stored_search_parameters = StoredSearchParameters.query.filter_by(
        collection=collection_id).all()
    for stored_search_parameter in stored_search_parameters:
        db.session.delete(stored_search_parameter)
        num_deleted += 1
    db.session.commit()
    return num_deleted


def _update_stac_data_using_selective_ingester_microservice(
        parameters) -> int:
    """Update stac data using the selective ingester microservice. Does not
    save the search parameters to the database as it is called from them
    anyways.

    :param parameters:  Parameters for the search from stac item-search standard
    :return: Response from the ingestion microservice
    """
    target_stac_api_url = current_app.config["TARGET_STAC_API_SERVER"]
    parameters["target_stac_catalog_url"] = target_stac_api_url
    parameters["update"] = True
    return _call_ingestion_microservice(parameters)


def _run_ingestion_task_force_update(
        stored_search_parameters: [StoredSearchParameters
                                   ]) -> list[int]:
    """ Calls the microservice on each set of StoredSearchParameters setting the update flag to true.

    :param stored_search_parameters: List of StoredSearchParameters to use for update operations
    :return: List of tuples containing the responses from the selective ingester microservice and the work id
    """
    responses_from_ingestion_microservice = []
    for i in stored_search_parameters:
        print("Updating with search parameters:", i)
        try:
            used_search_parameters = json.loads(i.used_search_parameters)
            used_search_parameters["update"] = True
            microservice_response = _update_stac_data_using_selective_ingester_microservice(
                used_search_parameters)
            responses_from_ingestion_microservice.append(
                microservice_response)
        except ValueError:
            pass
    return responses_from_ingestion_microservice
