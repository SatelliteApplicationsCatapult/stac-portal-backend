import azure.core.exceptions
from azure.storage.blob import BlobServiceClient
from flask import current_app


def check_blob_status():
    """Check if the blob storage is available.

    :return: A tuple containing the status and the message.
    """
    try:
        connection_string = current_app.config[
            "AZURE_STORAGE_CONNECTION_STRING"]
        print("Connection string: " + connection_string)
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string)
        # close the connection
        blob_service_client.close()

        return True, "Blob storage is available."
    except Exception as e:
        return False, str(e)


def upload_filestream_to_blob(filename: str, filestream) -> str:
    connection_string = current_app.config[
        "AZURE_STORAGE_CONNECTION_STRING"]
    print("Connection string: " + connection_string)
    blob_service_client = BlobServiceClient.from_connection_string(
        connection_string)
    container_name = current_app.config[
        "AZURE_STORAGE_BLOB_NAME_FOR_STAC_ITEMS"]
    if _does_file_exist_on_blob(filename):
        raise FileExistsError
    try:
        # stream the filestream into blob storage
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=filename)
        blob_client.upload_blob(filestream)
        stored_file_path = blob_client.url
        blob_service_client.close()
        return stored_file_path
    except azure.core.exceptions.ResourceExistsError:
        raise FileExistsError
    finally:
        blob_service_client.close()


def _does_file_exist_on_blob(filename: str):
    """Check if a filename exists on the blob storage.

    :param filename: The name of the filename to check.
    :return: A tuple containing the status and the message.
    """
    try:
        connection_string = current_app.config[
            "AZURE_STORAGE_CONNECTION_STRING"]
        print("Connection string: " + connection_string)
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string)
        container_name = current_app.config[
            "AZURE_STORAGE_BLOB_NAME_FOR_STAC_ITEMS"]

        try:
            blob_client = blob_service_client.get_blob_client(
                container=container_name, blob=filename)
            blob_client.get_blob_properties()
            blob_service_client.close()
            return True

        except azure.core.exceptions.ResourceNotFoundError as e:
            blob_service_client.close()
            return False
        finally:
            blob_service_client.close()

    except Exception as e:
        return False, str(e)