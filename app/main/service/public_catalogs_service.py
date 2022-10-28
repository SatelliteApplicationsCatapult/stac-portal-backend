import json
import logging
from threading import Thread
from typing import Dict, List

import geoalchemy2
import requests
import shapely
import sqlalchemy
from flask import current_app
from shapely.geometry import MultiPolygon
from shapely.geometry import box
from sqlalchemy import or_

from app.main.model.public_catalogs_model import PublicCatalog, PublicCollection
from .status_reporting_service import make_stac_ingestion_status_entry, set_stac_ingestion_status_entry
from .. import db
from ..custom_exceptions import *
from ..model.public_catalogs_model import StoredSearchParameters
from ..service import stac_service
from ..util import process_timestamp


def store_new_public_catalog(name: str, url: str, description: str, return_as_dict=True) -> Dict[
                                                                                                any, any] or PublicCatalog:
    """
    Store a new public catalog in the database.

    :param name: Name of the catalog
    :param url: Url of the catalog
    :param description: Description of the catalog
    :param return_as_dict: (True) Return the catalog as a dict, (False) return the catalog as a PublicCatalog object
    :return: The catalog as a dict or PublicCatalog object
    """
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


def store_publicly_available_catalogs() -> None:
    """
    Get all publicly available catalogs and store them in the database.

    :return: The number of catalogs stored
    """
    lookup_api: str = "https://stacindex.org/api/catalogs"
    response = requests.get(lookup_api)
    response_result = response.json()
    filtered_response_result = [i for i in response_result if i['isPrivate'] == False and i['isApi'] == True]
    results = []
    work = []

    # pool = multiprocessing.Pool(processes=4)
    # for catalog in filtered_response_result:
    #     work.append(
    #         pool.apply_async(_store_catalog_and_collections, (catalog['title'], catalog['url'], catalog['summary'])))
    # [work.wait() for work in work]
    # for work in work:
    #     results.append(work.get())
    def run_async(title, catalog_url, catalog_summary, results_list, app_for_context):
        with app_for_context.app_context():
            try:
                results_list.append(_store_catalog_and_collections(title, catalog_url, catalog_summary))
            except:
                results_list.append(None)

    app = current_app._get_current_object()  # TODO: Is there a better way to do this?
    for catalog in filtered_response_result:
        t = Thread(target=run_async, args=(catalog['title'], catalog['url'], catalog['summary'], results, app))
        t.start()
    # while len(results) < len(filtered_response_result):
    #     time.sleep(0.1)
    # number_of_catalogs = len([i for i in results if i is not None])
    # number_of_collections = sum([i for i in results if i is not None])
    # return number_of_catalogs, number_of_collections


def remove_all_public_catalogs() -> None:
    """
    Remove all public catalogs from the database.
    """
    db.session.query(PublicCatalog).delete()
    db.session.commit()


def get_public_collections():
    public_collections = PublicCollection.query.all()
    out = []
    for public_collection in public_collections:
        out.append(public_collection.as_dict())
    return out


def _is_catalog_public_and_valid(url: str) -> bool:
    """
    Check if a catalog is public and valid.

    For the catalog to be valid it must have at least one collection with at least one item.
    :param url: Url of the catalog
    :return: True if the catalog is public and valid, False otherwise
    """
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


def _store_collections(public_catalog_entry: PublicCatalog) -> int:
    """
    Store all collections for a catalog in the database.
    :param public_catalog_entry: PublicCatalog object
    :return: The number of collections stored
    """
    count_added = 0
    try:
        collections_for_new_catalog: List[
            Dict[any, any]] = _get_all_available_collections_from_public_catalog(public_catalog_entry)
        # for each new collection, store it in the database
        for collection in collections_for_new_catalog:
            # get a public_collection object using public_catalog_entry id and collection id
            public_collection: PublicCollection
            public_collection: PublicCollection = PublicCollection.query.filter_by(
                parent_catalog=public_catalog_entry.id, id=collection['id']).first()
            if public_collection:
                pass
                logging.log("Updating collection: " + collection['id'])

            else:
                logging.log("Creating new collection: " + collection['id'])
                public_collection: PublicCollection = PublicCollection()
                public_collection.id = collection['id']
            try:
                public_collection.type = collection['type']
            except KeyError:
                public_collection.type = "Collection"
            try:
                public_collection.title = collection['title']
            except KeyError:
                public_collection.title = None
            try:
                public_collection.description = collection['description']
            except:
                public_collection.description = None
            start_time_string = collection['extent']['temporal']['interval'][0][0]
            end_time_string = collection['extent']['temporal']['interval'][0][1]
            public_collection.temporal_extent_start = process_timestamp.process_timestamp_single_string(
                start_time_string)
            public_collection.temporal_extent_end = process_timestamp.process_timestamp_single_string(end_time_string)
            bboxes = collection['extent']['spatial']['bbox']
            shapely_boxes = []
            for i in range(0, len(bboxes)):
                shapely_box = box(*(collection['extent']['spatial']['bbox'][i]))
                shapely_boxes.append(shapely_box)
            shapely_multi_polygon = geoalchemy2.shape.from_shape(MultiPolygon(shapely_boxes), srid=4326)
            public_collection.spatial_extent = shapely_multi_polygon
            public_collection.parent_catalog = public_catalog_entry.id  # TODO: Rename to parent_catalog_id
            db.session.add(public_collection)
            count_added += 1
        db.session.commit()

    except ConvertingTimestampError:
        db.session.commit()
        raise ConvertingTimestampError
    except KeyError as e:
        db.session.commit()

    return count_added


def _store_catalog_and_collections(title, url, summary) -> int or None:
    """
    Store a catalog and all its collections in the database.

    :param title: Title of the catalog
    :param url: Url of the catalog
    :param summary: Summary of the catalog
    :return: Number of collections stored, None if the catalog is not public or valid
    """
    if not _is_catalog_public_and_valid(url):
        return None
    try:
        new_catalog: PublicCatalog = store_new_public_catalog(title, url, summary, return_as_dict=False)
        return _store_collections(new_catalog)
    except CatalogAlreadyExistsError:
        already_existing_catalog: PublicCatalog = PublicCatalog.query.filter_by(url=url).first()
        return _store_collections(already_existing_catalog)


def search_collections(bbox: shapely.geometry.polygon.Polygon or list[float], time_interval_timestamp: str,
                       public_catalog_id: int = None) -> dict[str, any] or list[any]:
    if public_catalog_id:
        try:
            get_public_catalog_by_id_as_dict(public_catalog_id)
        except CatalogDoesNotExistError:
            raise CatalogDoesNotExistError

    if isinstance(bbox, list):
        bbox = shapely.geometry.box(*bbox)
    a = db.session.query(PublicCollection).filter(PublicCollection.spatial_extent.ST_Intersects(
        f"SRID=4326;{bbox.wkt}"))
    if public_catalog_id:
        a = a.filter(PublicCollection.parent_catalog == public_catalog_id)
    time_start, time_end = process_timestamp.process_timestamp_dual_string(time_interval_timestamp)
    # all 4 cases of time_start and time_end
    if time_start and time_end:
        a = a.filter(
            or_(PublicCollection.temporal_extent_start <= time_end, PublicCollection.temporal_extent_start == None),
            or_(PublicCollection.temporal_extent_end >= time_start, PublicCollection.temporal_extent_end == None))
    elif time_start and not time_end:
        a = a.filter(
            or_(PublicCollection.temporal_extent_end >= time_start, PublicCollection.temporal_extent_end == None))
    elif not time_start and time_end:
        a = a.filter(
            or_(PublicCollection.temporal_extent_start <= time_end, PublicCollection.temporal_extent_start == None))
    else:
        pass
    data = a.all()
    # group data by parent_catalog parameter
    grouped_data = {}
    for item in data:
        item: PublicCollection
        if item.parent_catalog in grouped_data:
            grouped_data[item.parent_catalog]["collections"].append(item.as_dict())
        else:
            grouped_data[item.parent_catalog] = {}
            grouped_data[item.parent_catalog]["catalog"] = PublicCatalog.query.filter_by(
                id=item.parent_catalog).first().as_dict()
            grouped_data[item.parent_catalog]["collections"] = []
            grouped_data[item.parent_catalog]["collections"].append(item.as_dict())
    if not public_catalog_id:
        keys = list(grouped_data.keys())
        out = []
        for i in keys:
            out.append(grouped_data[i])
        return out
    else:
        try:
            return grouped_data[public_catalog_id]
        except KeyError:
            return []


def get_collections_from_public_catalog_id(public_catalog_id: int):
    try:
        get_public_catalog_by_id_as_dict(public_catalog_id)
    except CatalogDoesNotExistError:
        raise PublicCatalogDoesNotExistError
    data = PublicCollection.query.filter_by(parent_catalog=public_catalog_id).all()
    out = []
    for item in data:
        out.append(item.as_dict())
    return out


def get_all_stored_public_collections_as_list_of_dict():
    public_collections = PublicCollection.query.all()
    out = []
    for public_collection in public_collections:
        out.append(public_collection.as_dict())
    return out


def _get_all_available_collections_from_public_catalog(public_catalogue_entry: PublicCatalog) -> List[Dict[
    any, any]]:
    """
    Get all available collections from a public catalog.

    :param public_catalogue_entry: PublicCatalog object
    :return: List of all collections in the catalog
    """
    logging.info("Getting collections from catalog: " + public_catalogue_entry.name)
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
                logging.info("Skipping collection without item link: " + collection['title'])
                continue
            # if item link is found, check if it is empty
            item_link_response = requests.get(item_link)
            if item_link_response.status_code != 200:
                logging.info("Skipping collection with not-public item link: " + collection['title'])
                continue
            item_link_response_json = item_link_response.json()
            if len(item_link_response_json['features']) == 0:
                logging.info("Skipping empty collection: " + collection['title'])
                continue
            collections_to_return.append(collection)
        except Exception as e:
            logging.error("Skipping collection with error: " + collection['title'])
            logging.error(e)
    return collections_to_return


def get_all_stored_public_catalogs_as_list_of_dict() -> List[Dict[any, any]]:
    """
    Get all stored public catalogs as a list of dictionaries.
    :return: Public catalogs as a list of dictionaries
    """
    a: [PublicCatalog] = PublicCatalog.query.all()
    data = []
    for item in a:
        x = item.as_dict()
        x["stored_search_parameters"] = get_all_stored_search_parameters(item.id)
        data.append(x)
    return data


def get_public_catalog_by_id_as_dict(public_catalog_id: int) -> Dict[any, any]:
    """
    Get a public catalog by its id as a dictionary.
    :param public_catalog_id: Id of the public catalog
    :return: Catalog as a dictionary
    """
    try:
        a: PublicCatalog = PublicCatalog.query.filter_by(
            id=public_catalog_id).first()
        return a.as_dict()
    except AttributeError:
        raise CatalogDoesNotExistError


def remove_public_catalog_via_catalog_id(public_catalog_id: int) -> Dict[any, any]:
    """
    Remove a public catalog by its id.
    :param public_catalog_id: Id of the public catalog to remove
    :return: Dictionary representation of the removed catalog
    """
    try:
        a: PublicCatalog = PublicCatalog.query.filter_by(
            id=public_catalog_id).first()
        db.session.delete(a)
        db.session.commit()
        return a.as_dict()
    except sqlalchemy.orm.exc.UnmappedInstanceError as e:
        raise CatalogDoesNotExistError


def load_specific_collections_via_catalog_id(catalog_id: int,
                                             parameters: Dict[any, any] = None):
    """
    Load specific collections from a catalog into the database.
    :param catalog_id: Catalog id of the catalog to load collections from
    :param parameters: STAC Filter parameters
    :return: Id of the created work session for which status can be obtained
    """
    public_catalogue_entry: PublicCatalog = PublicCatalog.query.filter_by(
        id=catalog_id).first()
    if public_catalogue_entry is None:
        raise CatalogDoesNotExistError
    if parameters is None:
        parameters = {}
    parameters['source_stac_catalog_url'] = public_catalogue_entry.url
    target_stac_api_url = current_app.config['TARGET_STAC_API_SERVER']
    _store_search_parameters(catalog_id, parameters)
    parameters["target_stac_catalog_url"] = target_stac_api_url
    return _call_ingestion_microservice(parameters)


def update_all_stac_records() -> list[int]:
    """
    Update all STAC records in the database.
    :return: Updated collection ids
    """
    stored_search_parameters: [StoredSearchParameters
                               ] = StoredSearchParameters.query.all()
    return _run_ingestion_task_force_update(stored_search_parameters)


def update_specific_collections_via_catalog_id(catalog_id: int,
                                               collections: [str] = None
                                               ) -> list[int]:
    """
    Update specific collections from a catalog into the database.
    :param catalog_id: Catalog id of the catalog to update collections from
    :param collections: List of collection ids to update
    :return: Updated collection ids
    """
    logging.log("Updating collections for catalogue id: " + str(catalog_id))
    public_catalogue_entry: PublicCatalog = PublicCatalog.query.filter_by(
        id=catalog_id).first()

    if public_catalogue_entry is None:
        raise CatalogDoesNotExistError("No catalogue entry found for id: " +
                                       str(catalog_id))
    stored_search_parameters: [StoredSearchParameters
                               ] = StoredSearchParameters.query.filter_by(
        associated_catalog_id=catalog_id).all()
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
    """
    Call the ingestion microservice to load collections into the database.

    Also saves the search parameters used to load the collections into the database so
    the update can be called using the same parameters.

    :param parameters: STAC Filter parameters
    :return: Work session id which can be used to check the status of the ingestion
    """
    souce_stac_catalog_url = parameters['source_stac_catalog_url']
    target_stac_catalog_url = current_app.config['TARGET_STAC_API_SERVER']
    update = parameters['update']
    callback_id = make_stac_ingestion_status_entry(souce_stac_catalog_url, target_stac_catalog_url, update)
    parameters['callback_id'] = callback_id
    microservice_endpoint = current_app.config['STAC_SELECTIVE_INGESTER_ENDPOINT']

    def run_async(_parameters, _app):
        try:
            response = requests.post(
                microservice_endpoint,
                json=_parameters, timeout=None)
            if response.status_code != 200:
                error_msg = response.text
                with _app.app_context():
                    set_stac_ingestion_status_entry(int(callback_id), error_message=error_msg)
                    return
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
            with _app.app_context():
                err = str({
                    "error": "Unable to reach ingestion microservice"
                })
                set_stac_ingestion_status_entry(int(callback_id), error_message=err)
            logging.error("Error: " + str(e))

    app = current_app._get_current_object()  # TODO: Is there a better way to do this?
    thread = Thread(target=run_async, args=(parameters, app))
    thread.start()
    return callback_id


def _store_search_parameters(associated_catalogue_id,
                             parameters: dict) -> None:
    """
    Store the search parameters used to load the collections into the database.

    :param associated_catalogue_id: Catalogue id of the catalogue the collections were loaded from
    :param parameters: STAC Filter parameters
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
        except sqlalchemy.exc.IntegrityError:
            # exact same search parameters already exist, no need to store them again
            pass
        finally:
            db.session.rollback()


def remove_search_params_for_collection_id(collection_id: str) -> int:
    """
    Remove search parameters for a collection id.

    :param collection_id: Collection id to remove search parameters for
    :return: Number of search parameters removed
    """
    num_deleted = 0
    stored_search_parameters = StoredSearchParameters.query.filter_by(
        collection=collection_id).all()
    for stored_search_parameter in stored_search_parameters:
        db.session.delete(stored_search_parameter)
        num_deleted += 1
    db.session.commit()
    return num_deleted


def _run_ingestion_task_force_update(
        stored_search_parameters: [StoredSearchParameters
                                   ]) -> list[int]:
    """
    Run the ingestion task for a list of stored search parameters but force update.

    :param stored_search_parameters: List of stored search parameters to run the ingestion task for
    :return: List of work session ids which can be used to check the status of the ingestion
    """
    responses_from_ingestion_microservice = []
    for i in stored_search_parameters:
        try:
            used_search_parameters = json.loads(i.used_search_parameters)
            used_search_parameters["target_stac_catalog_url"] = current_app.config["TARGET_STAC_API_SERVER"]
            used_search_parameters["update"] = True
            microservice_response = _call_ingestion_microservice(
                used_search_parameters)
            responses_from_ingestion_microservice.append(
                microservice_response)
        except ValueError:
            pass
    return responses_from_ingestion_microservice


def remove_collection_from_public_catalog(catalog_id: int, collection_id: str):
    """
    Remove a collection from the public catalog.

    :param catalog_id: Catalog id of the public catalog
    :param collection_id: Collection id to remove from the public catalog
    """
    public_catalog = PublicCollection.query.filter_by(parent_catalog=catalog_id, id=collection_id).first()
    if public_catalog is None:
        raise PublicCollectionDoesNotExistError
    db.session.delete(public_catalog)
    db.session.commit()
    try:
        return stac_service.remove_public_collection_by_id_on_stac_api(collection_id)
    except CollectionDoesNotExistError:
        pass
    return "Collection does not exist on STAC API"


def get_all_stored_search_parameters(public_catalog_id: int = None) -> [Dict[any, any]]:
    """
    Get all stored search parameters.

    :param public_catalog_id: Public catalog id to get stored search parameters for
    :return: List of stored search parameters
    """
    public_catalog = PublicCatalog.query.filter_by(id=public_catalog_id).first()
    if public_catalog is None:
        raise PublicCatalogDoesNotExistError
    if public_catalog_id is None:
        data = StoredSearchParameters.query.all()
        return_data = []
        for i in data:
            return_data.append(i.to_dict())
    else:
        data = StoredSearchParameters.query.filter_by(associated_catalog_id=public_catalog_id).all()
        return [i.as_dict() for i in data]


def run_search_parameters(parameter_id: int) -> int:
    """
    Run a search parameter.

    :param parameter_id: Id of the search parameter to run
    :return: Work session id
    """
    stored_search_parameters = StoredSearchParameters.query.filter_by(id=parameter_id).first()
    if stored_search_parameters is None:
        raise StoredSearchParametersDoesNotExistError
    try:
        used_search_parameters = json.loads(stored_search_parameters.used_search_parameters)
        used_search_parameters["target_stac_catalog_url"] = current_app.config["TARGET_STAC_API_SERVER"]
        used_search_parameters["update"] = True
        microservice_response = _call_ingestion_microservice(used_search_parameters)
        return microservice_response
    except ValueError:
        pass
