import datetime
import json
from threading import Thread
from typing import Dict, List

import geoalchemy2
import requests
import sqlalchemy
from flask import current_app
from shapely.geometry import MultiPolygon
from shapely.geometry import box

from app.main.model.public_catalogs_model import PublicCatalog, PublicCollection
from .status_reporting_service import make_stac_ingestion_status_entry, set_stac_ingestion_status_entry
from .. import db
from ..custom_exceptions import *
from ..model.public_catalogs_model import StoredSearchParameters

_stored_collection_count = 0


def store_new_public_catalog(name: str, url: str, description: str, return_as_dict=True) -> Dict[
                                                                                                any, any] or PublicCatalog:
    try:
        a: PublicCatalog = PublicCatalog()
        a.name = name
        a.url = url
        a.description = description
        db.session.add(a)
        db.session.commit()
        if return_as_dict:
            return a.as_dict()
        else:
            return a
    except sqlalchemy.exc.IntegrityError:
        # rollback the session
        db.session.rollback()
        raise CatalogAlreadyExistsError


def store_publicly_available_catalogs() -> int:
    lookup_api: str = "https://stacindex.org/api/catalogs"
    response = requests.get(lookup_api)
    response_result = response.json()
    filtered_response_result = [i for i in response_result if i['isPrivate'] == False and i['isApi'] == True]
    results = []
    for catalog in filtered_response_result:
        results.append((_store_catalog_and_collections(
            catalog['title'], catalog['url'], catalog['summary'])))
    print("Stored collections count: " + str(_stored_collection_count))
    return len([i for i in results if i is not None])


def remove_all_catalogs():
    db.session.query(PublicCatalog).delete()
    db.session.commit()


def _is_catalog_public_and_valid(url: str) -> bool:
    url_removed_slash = url[:-1] if url.endswith('/') else url
    response = requests.get(url_removed_slash + '/collections')
    if response.status_code != 200:
        return False
    if len(response.json()['collections']) == 0:
        return False
    response_2 = requests.get(url_removed_slash + '/search?limit=1')
    if response_2.status_code != 200:
        return False
    if len(response_2.json()['features']) != 1:
        return False
    return True


def _store_collections(catalog_entry: PublicCatalog) -> int:
    count_added = 0
    try:
        collections_for_new_catalog: List[
            Dict[any, any]] = _get_all_available_collections_from_public_catalog(catalog_entry)
        # for each new collection, store it in the database
        for collection in collections_for_new_catalog:
            # get a public_collection object using catalog_entry id and collection id
            public_collection: PublicCollection
            public_collection: PublicCollection = PublicCollection.query.filter_by(
                parent_catalog=catalog_entry.id, id=collection['id']).first()
            if public_collection:
                print("Updating collection: " + collection['id'])

            else:
                print("Creating new collection: " + collection['id'])
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
                public_collection.temporal_extent_start = None
                for fmt in potential_datetime_formats:
                    try:
                        public_collection.temporal_extent_start = datetime.datetime.strptime(start_time_string, fmt)
                        break
                    except ValueError:
                        continue
                if public_collection.temporal_extent_start is None:
                    raise ConvertingTimestampError
            if end_time_string is not None:
                public_collection.temporal_extent_end = None
                for fmt in potential_datetime_formats:
                    try:
                        public_collection.temporal_extent_end = datetime.datetime.strptime(end_time_string, fmt)
                        break
                    except ValueError:
                        continue
                if public_collection.temporal_extent_end is None:
                    raise ConvertingTimestampError
            bboxes = collection['extent']['spatial']['bbox']
            shapely_boxes = []
            for i in range(0, len(bboxes)):
                shapely_box = box(*(collection['extent']['spatial']['bbox'][i]))
                shapely_boxes.append(shapely_box)
            shapely_multi_polygon = geoalchemy2.shape.from_shape(MultiPolygon(shapely_boxes))
            public_collection.spatial_extent = shapely_multi_polygon
            public_collection.parent_catalog = catalog_entry.id  # TODO: Rename to parent_catalog_id
            db.session.add(public_collection)
            count_added += 1
        db.session.commit()

    except ConvertingTimestampError:
        print("Could not convert timestamp")
        db.session.commit()
        raise ConvertingTimestampError
    except KeyError as e:
        db.session.commit()
        print("Url of problem catalog: " + catalog_entry.url)
        print(e)

    return count_added


def _store_catalog_and_collections(title, url, summary) -> int or None:
    print("Storing catalog and collections: " + title)
    if not _is_catalog_public_and_valid(url):
        return None
    try:
        new_catalog: PublicCatalog = store_new_public_catalog(title, url, summary, return_as_dict=False)
        return _store_collections(new_catalog)
    except CatalogAlreadyExistsError:
        already_existing_catalog: PublicCatalog = PublicCatalog.query.filter_by(url=url).first()
        return _store_collections(already_existing_catalog)
    except Exception as e:
        print(e)
        return None


def _get_all_available_collections_from_public_catalog(public_catalogue_entry: PublicCatalog) -> List[Dict[
    any, any]] or None:
    """Get all collections from a catalog specified by its id."""
    print("Getting collections from catalog: " + public_catalogue_entry.name)
    url = public_catalogue_entry.url
    # if url ends with /, remove it
    if url.endswith('/'):
        url = url[:-1]
    collections_url = url + '/collections'
    response = requests.get(collections_url)
    response_result = response.json()
    # for each collection, check if it is empty
    collections = response_result['collections']
    collections_to_return = []
    for collection in collections:
        try:
            print("Doing collection: " + collection['title'])
            # get the item link
            links = collection['links']
            # find link with rel type 'item'
            item_link = None
            for link in links:
                if link['rel'] == 'items':
                    item_link = link['href']
                    break
            # if item link is not found, skip this collection
            if item_link is None:
                print("Skipping collection without item link: " + collection['title'])
                continue
            # if item link is found, check if it is empty
            item_link_response = requests.get(item_link)
            if item_link_response.status_code != 200:
                print("Skipping collection with not-public item link: " + collection['title'])
                continue
            item_link_response_json = item_link_response.json()
            if len(item_link_response_json['features']) == 0:
                print("Skipping empty collection: " + collection['title'])
                continue
            collections_to_return.append(collection)
        except Exception as e:
            print("Skipping collection with error: " + collection['title'])
            print(e)
    global _stored_collection_count
    _stored_collection_count += len(collections_to_return)
    return collections_to_return


def get_all_available_collections_from_all_public_catalogs() -> List[List[Dict[any, any]]]:
    """Get all collections from all public catalogs."""
    data = []
    public_catalogs: [PublicCatalog] = PublicCatalog.query.all()
    for public_catalog in public_catalogs:
        data.append((_get_all_available_collections_from_public_catalog(public_catalog)))
    # return data where not None
    return [i for i in data if i is not None]


def get_all_available_collections_from_all_public_catalogs_filter_via_polygon(polygons) -> List[str]:
    pass


def get_all_stored_public_catalogs_as_list_of_dict() -> List[Dict[any, any]]:
    a: [PublicCatalog] = PublicCatalog.query.all()
    return [i.as_dict() for i in a]


def get_public_catalog_by_id_as_dict(public_catalog_id: int) -> Dict[any, any]:
    try:
        a: PublicCatalog = PublicCatalog.query.filter_by(
            id=public_catalog_id).first()
        return a.as_dict()
    except AttributeError:
        raise CatalogDoesNotExistError


def remove_public_catalog_via_catalog_id(public_catalog_id: int) -> Dict[any, any]:
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
    stored_search_parameters: [StoredSearchParameters
                               ] = StoredSearchParameters.query.all()
    return _run_ingestion_task_force_update(stored_search_parameters)


def update_specific_collections_via_catalog_id(catalog_id: int,
                                               collections: [str] = None
                                               ) -> list[int]:
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
            # if any collection in used_search_parameters_collections is in collections, then add to
            # stored_search_parameters_to_run
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
    target_stac_api_url = current_app.config["TARGET_STAC_API_SERVER"]
    parameters["target_stac_catalog_url"] = target_stac_api_url
    parameters["update"] = True
    return _call_ingestion_microservice(parameters)


def _run_ingestion_task_force_update(
        stored_search_parameters: [StoredSearchParameters
                                   ]) -> list[int]:
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
