import json
from typing import Dict, Tuple, List
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__

import requests
import sqlalchemy
from flask import current_app

from .. import db
from ..model.file_upload_model import *

# Create the BlobServiceClient object which will be used to create a container client
# blob_service_client = BlobServiceClient.from_connection_string(current_app.config["AZURE_STORAGE_CONNECTION_STRING"])
#
# # Create a unique name for the container
# container_name = current_app.config["AZURE_STORAGE_BLOB_NAME_FOR_STAC_ITEMS"]
#
# # Create the container
# container_client = blob_service_client.create_container(container_name)

def check_blob_status():
    """Check if the blob storage is available.
    :return: A tuple containing the status and the message.
    """
    try:
        connection_string = current_app.config["AZURE_STORAGE_CONNECTION_STRING"]
        print("Connection string: " + connection_string)
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = current_app.config["AZURE_STORAGE_BLOB_NAME_FOR_STAC_ITEMS"]
        container_client = blob_service_client.get_container_client(container_name)
        # close the connection
        blob_service_client.close()

        return True, "Blob storage is available."
    except Exception as e:
        return False, str(e)

    
