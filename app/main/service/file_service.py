import os

import azure.core.exceptions
from azure.storage.blob import BlobServiceClient
from flask import current_app
from werkzeug.utils import secure_filename


def check_blob_status():
    """Check if the blob storage is available.
    :return: A tuple containing the status and the message.
    """
    try:
        connection_string = current_app.config["AZURE_STORAGE_CONNECTION_STRING"]
        print("Connection string: " + connection_string)
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        # close the connection
        blob_service_client.close()

        return True, "Blob storage is available."
    except Exception as e:
        return False, str(e)


def _upload_file_to_blob(filename, blob_name=None):
    """Upload a file to the blob storage.
    :param filename: The file to upload.
    :return: A tuple containing the status and the message.
    """
    if not blob_name:
        blob_name = filename
    try:
        connection_string = current_app.config["AZURE_STORAGE_CONNECTION_STRING"]
        print("Connection string: " + connection_string)
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = current_app.config["AZURE_STORAGE_BLOB_NAME_FOR_STAC_ITEMS"]

        try:
            with open(filename, "rb") as data:
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
                blob_client.upload_blob(data)
                stored_file_path = blob_client.url
            blob_service_client.close()
            return True, stored_file_path

        except azure.core.exceptions.ResourceExistsError as e:
            blob_service_client.close()
            return False, "File already exists in blob storage."
        finally:
            blob_service_client.close()

    except Exception as e:
        return False, str(e)


def stage_file(item_id: str, file):
    filename = secure_filename(file.filename)
    # if item_id is not present in the filename, prepend it
    if item_id not in filename:
        filename = item_id + "_" + filename

    if _does_file_exist_on_blob(filename):
        raise FileExistsError("File already exists in blob storage.")

    return _save_file(file, filename)


def upload_staged_files_to_blob(item_id: str) -> list[str]:
    files = list_staged_files(item_id)
    urls = []
    for filename in files:
        status, filepath = _upload_file_to_blob("./stage/" + filename, filename)
        urls.append(filepath)
        # remove the file from the stage directory
        _delete_file(filename)
    return urls


def list_staged_files(item_id: str) -> list[str]:
    files = []
    for filename in os.listdir("./stage"):
        if item_id in filename:
            files.append(filename)
    return files


def _save_file(file, filename, prefix="stage") -> str:
    # if stage directory does not exist, create it
    if not os.path.exists("./stage"):
        os.makedirs("./stage")
    new_filename = "./" + prefix + "/" + filename
    file.save(new_filename)
    return new_filename


def _delete_file(filename, prefix="stage"):
    new_filename = "./" + prefix + "/" + filename
    os.remove(new_filename)


def unstage_all_files(item_id: str):
    for filename in os.listdir("./stage"):
        if item_id in filename:
            _delete_file(filename)


def _does_file_exist_on_blob(filename: str):
    """Check if a filename exists on the blob storage.
    :param filename: The name of the filename to check.
    :return: A tuple containing the status and the message.
    """
    try:
        connection_string = current_app.config["AZURE_STORAGE_CONNECTION_STRING"]
        print("Connection string: " + connection_string)
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = current_app.config["AZURE_STORAGE_BLOB_NAME_FOR_STAC_ITEMS"]

        try:
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)
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
