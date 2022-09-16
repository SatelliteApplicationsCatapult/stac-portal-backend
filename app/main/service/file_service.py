import azure.core.exceptions
from azure.storage.blob import BlobServiceClient
from flask import current_app


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
        # close the connection
        blob_service_client.close()

        return True, "Blob storage is available."
    except Exception as e:
        return False, str(e)


def upload_file_to_blob(file):
    """Upload a file to the blob storage.
    :param file: The file to upload.
    :return: A tuple containing the status and the message.
    """
    try:
        connection_string = current_app.config["AZURE_STORAGE_CONNECTION_STRING"]
        print("Connection string: " + connection_string)
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = current_app.config["AZURE_STORAGE_BLOB_NAME_FOR_STAC_ITEMS"]

        try:
            with open(file.filename, "rb") as data:
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
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
