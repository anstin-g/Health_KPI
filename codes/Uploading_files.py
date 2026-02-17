from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient
import os
import logging



# Initialize BlobServiceClient
blob_service_client = BlobServiceClient(account_url=BLOB_ACCOUNT_URL, credential=STORAGE_ACCOUNT_KEY)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Assuming blob_service_client and BLOB_CONTAINER_NAME are already defined elsewhere

def create_directory_if_not_exists(directory_name):
    """Creates a directory (virtual folder) in the Azure Blob container if it doesn't exist."""
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
    
    blob_name = f"{directory_name}/"
    blobs = container_client.list_blobs(name_starts_with=blob_name)

    if not any(blobs):  # If no blobs exist in this folder, create a dummy blob
        dummy_blob_client = container_client.get_blob_client(blob_name + ".placeholder")
        dummy_blob_client.upload_blob(b"", overwrite=True)
        logger.info(f"Created directory: {directory_name}")

def upload_document_to_blob(directory_name, local_file_path):
    """Uploads a document to the specified directory in Azure Blob Storage."""
    blob_name = f"{directory_name}/{os.path.basename(local_file_path)}"
    blob_client = blob_service_client.get_blob_client(BLOB_CONTAINER_NAME, blob_name)

    with open(local_file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
        logger.info(f"Uploaded: {local_file_path} to {blob_name}")

def delete_documents_in_directory(directory_name):
    """Deletes all documents in the specified directory within the Azure Blob container."""
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
    blobs = container_client.list_blobs(name_starts_with=f"{directory_name}/")

    for blob in blobs:
        blob_client = container_client.get_blob_client(blob)
        blob_client.delete_blob()
        logger.info(f"Deleted: {blob.name}")

def delete_file_in_directory(directory_name, file_name):
    """Deletes a specific file inside a directory in the Azure Blob container."""
    blob_name = f"{directory_name}/{file_name}"
    blob_client = blob_service_client.get_blob_client(BLOB_CONTAINER_NAME, blob_name)

    try:
        blob_client.delete_blob()
        logger.info(f"Deleted file: {blob_name}")
    except Exception as e:
        logger.error(f"Error deleting file: {blob_name} - {e}")

def list_documents_in_directory(directory_name):
    """Lists all document names in the specified directory within the Azure Blob container."""
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
    blobs = container_client.list_blobs(name_starts_with=f"{directory_name}/")

    document_list = [blob.name for blob in blobs]
    logger.info(f"Listed documents in directory '{directory_name}': {document_list}")
    
    return document_list

# Example Usage:
# create_directory_if_not_exists("3")
# upload_document("project_docs", r"C:\Users\DELL\Downloads\DOC_1.pdf")
# delete_documents_in_directory("project_docs")
# delete_file_in_directory("project_docs","DOC_1.pdf")
# print(list_documents_in_directory('3'))
