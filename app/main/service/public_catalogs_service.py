import json
from typing import Dict, List

import requests
import sqlalchemy
from flask import current_app

from app.main.model.public_catalogs_model import PublicCatalog
from .status_reporting_service import make_stac_ingestion_status_entry, set_stac_ingestion_status_entry
from .. import db
from ..custom_exceptions import *
from ..model.public_catalogs_model import StoredSearchParameters


def store_new_public_catalog(name: str, url: str, description: str,
                             stac_version: str) -> Dict[any, any]:
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
        a.stac_version = stac_version
        db.session.add(a)
        db.session.commit()
        return a.as_dict()
    except sqlalchemy.exc.IntegrityError:
        raise CatalogAlreadyExistsError


def get_all_public_catalogs() -> List[Dict[any, any]]:
    """Get all public catalogs from the database.

    :return: List of all public catalogs as list of dicts
    """
    a: PublicCatalog = PublicCatalog.query.all()
    return [i.as_dict() for i in a]


def get_public_catalog_by_id(public_catalog_id: int) -> Dict[any, any]:
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


def remove_public_catalog_by_id(public_catalog_id: int) -> Dict[any, any]:
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


def get_specific_collections_via_catalog_id(catalog_id: int,
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
    return _call_ingestion_microservice(parameters)


def update_all_stac_records() -> list[str]:
    """Run the search using every stored search parameter.

    :return: List of tuples containing the responses from the selective ingester microservice and the work id
    """
    stored_search_parameters: [StoredSearchParameters
                               ] = StoredSearchParameters.query.all()
    return _run_ingestion_task_force_update(stored_search_parameters)


def update_specific_collections_via_catalog_id(catalog_id: int,
                                               collections: [str] = None
                                               ) -> list[str]:
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


def _call_ingestion_microservice(parameters) -> str:
    souce_stac_catalog_url = parameters['source_stac_catalog_url']
    target_stac_catalog_url = current_app.config['TARGET_STAC_API_SERVER']
    update = parameters['update']
    callback_id = make_stac_ingestion_status_entry(souce_stac_catalog_url, target_stac_catalog_url, update)
    parameters['callback_id'] = callback_id
    microservice_endpoint = current_app.config['STAC_SELECTIVE_INGESTER_ENDPOINT']
    try:
        response = requests.post(
            microservice_endpoint,
            json=parameters, timeout=None)
        # convert response to json
        response_json = response.json()
        newly_stored_collections = response_json['newly_stored_collections']
        newly_stored_collections_count = response_json['newly_stored_collections_count']
        updated_collections_count = response_json['updated_collections_count']
        updated_collections = response_json['updated_collections']
        newly_stored_items_count = response_json['newly_stored_items_count']
        updated_items_count = response_json['updated_items_count']
        already_stored_items_count = response_json['already_stored_items_count']
        set_stac_ingestion_status_entry(int(callback_id), newly_stored_collections_count, newly_stored_collections,
                                        updated_collections_count, updated_collections, newly_stored_items_count,
                                        updated_items_count, already_stored_items_count)
        return response_json

    except Exception as e:
        print("Error: " + str(e))
        raise ConnectionError("Could not connect to stac selective ingester microservice")


def _store_search_parameters(associated_catalogue_id,
                             parameters: dict) -> None:
    """Store the search parameters in the database so they can be used to
    update the data later on.

    Separate each collection into it's own search parameter so they can be updated individually with ease.

    :param associated_catalogue_id:
    :param parameters:
    :return:
    """
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
        parameters) -> str:
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
                                   ]) -> list[str]:
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
