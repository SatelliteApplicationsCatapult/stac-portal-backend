import json
from typing import Dict, Tuple, List

import requests
import sqlalchemy
from flask import current_app

from app.main.model.public_catalogs_model import PublicCatalog
from .status_reporting_service import _make_stac_ingestion_status_entry
from .. import db
from ..model.public_catalogs_model import StoredSearchParameters
from ..util.get_ip_from_cird_range import get_ip_from_cird_range


def store_new_public_catalog(name: str, url: str, description: str,
                             stac_version: str) -> Dict[any, any]:
    """Store a new public catalog in the database.

    :param name: Name of the catalog
    :param url: URL of the catalog, to stac api root
    :param description: Description of the catalog
    :param stac_version: Stac version catalogue used
    :return: New catalogue parameters from database as dict
    """
    a: PublicCatalog = PublicCatalog()
    a.name = name
    a.url = url
    a.description = description
    a.stac_version = stac_version
    db.session.add(a)
    db.session.commit()
    return a.as_dict()


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
    a: PublicCatalog = PublicCatalog.query.filter_by(
        id=public_catalog_id).first()
    return a.as_dict()


def remove_public_catalog_by_id(public_catalog_id: int) -> Dict[any, any]:
    """Remove a public catalog by its id.

    :param public_catalog_id: Id of the public catalog
    :return: Public catalog as dict
    """
    a: PublicCatalog = PublicCatalog.query.filter_by(
        id=public_catalog_id).first()
    db.session.delete(a)
    db.session.commit()
    return a.as_dict()


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
        raise LookupError("No catalogue entry found for id: " +
                          str(catalog_id))
    if parameters is None:
        parameters = {}
    parameters['source_stac_catalog_url'] = public_catalogue_entry.url
    return _ingest_stac_data_using_selective_ingester_microservice(parameters)


def update_all_stac_records() -> List[Tuple[str, int]]:
    """Run the search using every stored search parameter.

    :return: List of tuples containing the responses from the selective ingester microservice and the work id
    """
    stored_search_parameters: [StoredSearchParameters
                               ] = StoredSearchParameters.query.all()
    return _run_ingestion_task_force_update(stored_search_parameters)


def update_specific_collections_via_catalog_id(catalog_id: int,
                                               collections: [str] = None
                                               ) -> List[Tuple[str, int]]:
    """Get all stored search parameters for a specific catalogue id. Then
    combine them all together and pass on for update.

    :param catalog_id: Catalogue id to update it's collections
    :param collections: Specific collections to update. If None, all collections will be updated
    :return: List of tuples containing the responses from the selective ingester microservice and the work id
    """
    public_catalogue_entry: PublicCatalog = PublicCatalog.query.filter_by(
        id=catalog_id).first()

    if public_catalogue_entry is None:
        raise LookupError("No catalogue entry found for id: " +
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
            # if any collection in used_search_parameters_collections is in collections, then add to stored_search_parameters_to_run
            check = any(item in used_search_parameters_collections
                        for item in collections)
            if check:
                # TODO: This updates all collections from the stored search parameter, not just the ones specified
                # TODO: Either store each collection in each search param separately or update the search param to only contain the collections specified
                stored_search_parameters_to_run.append(stored_search_parameter)

        return _run_ingestion_task_force_update(
            stored_search_parameters_to_run)


def _ingest_stac_data_using_selective_ingester_microservice(
        parameters) -> [str, int]:
    """Ingest stac data using the selective ingester microservice. Saves the
    search parameters to the database so the data can be updated later on.

    :param parameters: Parameters for the search from stac item-search standard
    :return: Response from the ingestion microservice
    """
    source_stac_api_url = parameters['source_stac_catalog_url']
    target_stac_api_url = "https://stac-api-server.azurewebsites.net"
    update = parameters['update']
    status_id, associated_catalogue_id = _make_stac_ingestion_status_entry(
        source_stac_api_url, target_stac_api_url, update)

    try:
        stored_search_parameters = StoredSearchParameters()
        stored_search_parameters.associated_catalog_id = associated_catalogue_id
        stored_search_parameters.used_search_parameters = json.dumps(
            parameters)
        db.session.add(stored_search_parameters)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        # exact same search parameters already exist, no need to store them again
        pass
    finally:
        # roolback if there is an error
        db.session.rollback()

    parameters["target_stac_catalog_url"] = target_stac_api_url
    parameters["callback_endpoint"] = current_app.config[
        "STAC_SELECTIVE_INGESTER_CALLBACK_ENDPOINT"] + "/" + str(status_id)

    cidr_range_for_stac_selective_ingester = current_app.config[
        'STAC_SELECTIVE_INGESTER_CIDR_RANGE']
    port_for_stac_selective_ingester = current_app.config[
        'STAC_SELECTIVE_INGESTER_PORT']
    protocol_for_stac_selective_ingester = current_app.config[
        'STAC_SELECTIVE_INGESTER_PROTOCOL']

    potential_ips = get_ip_from_cird_range(
        cidr_range_for_stac_selective_ingester, remove_unusable=True)

    for ip in potential_ips:
        print("Trying to connect to: ", ip)
        try:
            response = requests.post(
                protocol_for_stac_selective_ingester + "://" + ip + ":" +
                str(port_for_stac_selective_ingester) + "/ingest",
                json=parameters)
            return response.text, status_id
        except requests.exceptions.ConnectionError:
            continue


def _update_stac_data_using_selective_ingester_microservice(
        parameters) -> [str, int]:
    """Update stac data using the selective ingester microservice. Does not
    save the search parameters to the database as it is called from them
    anyways.

    :param parameters:  Parameters for the search from stac item-search standard
    :return: Response from the ingestion microservice
    """
    source_stac_api_url = parameters['source_stac_catalog_url']
    target_stac_api_url = current_app.config["TARGET_STAC_API_SERVER"]
    update = True
    status_id, associated_catalogue_id = _make_stac_ingestion_status_entry(
        source_stac_api_url, target_stac_api_url, update)

    parameters["target_stac_catalog_url"] = target_stac_api_url
    parameters["callback_endpoint"] = current_app.config[
        "STAC_SELECTIVE_INGESTER_CALLBACK_ENDPOINT"] + "/" + str(status_id)

    cidr_range_for_stac_selective_ingester = current_app.config[
        'STAC_SELECTIVE_INGESTER_CIDR_RANGE']
    port_for_stac_selective_ingester = current_app.config[
        'STAC_SELECTIVE_INGESTER_PORT']
    protocol_for_stac_selective_ingester = current_app.config[
        'STAC_SELECTIVE_INGESTER_PROTOCOL']

    potential_ips = get_ip_from_cird_range(
        cidr_range_for_stac_selective_ingester, remove_unusable=True)

    for ip in potential_ips:
        print("Trying to connect to: ", ip)
        try:
            response = requests.post(
                protocol_for_stac_selective_ingester + "://" + ip + ":" +
                str(port_for_stac_selective_ingester) + "/ingest",
                json=parameters)
            return response.text, status_id
        except requests.exceptions.ConnectionError:
            continue


def _run_ingestion_task_force_update(
    stored_search_parameters: [StoredSearchParameters
                               ]) -> List[Tuple[str, int]]:
    """Calls the _update_stac_data_using_selective_ingester_microservice on
    each set of StoredSearchParameters setting the update flag to true.

    :param stored_search_parameters: List of StoredSearchParameters to use for update operations
    :return: List of tuples containing the responses from the selective ingester microservice and the work id
    """
    responses_from_ingestion_microservice = []
    for i in stored_search_parameters:
        try:
            used_search_parameters = json.loads(i.used_search_parameters)
            used_search_parameters["update"] = True
            microservice_response, work_id = _update_stac_data_using_selective_ingester_microservice(
                used_search_parameters)
            responses_from_ingestion_microservice.append(
                (microservice_response, work_id))
        except ValueError:
            pass
    return responses_from_ingestion_microservice
