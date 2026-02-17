from django.http import HttpResponse, Http404
from azure.storage.blob import BlobServiceClient
import mimetypes
import logging

# Azure Blob configuration (same as in your working code)

blob_service_client = BlobServiceClient(account_url=BLOB_ACCOUNT_URL, credential=STORAGE_ACCOUNT_KEY)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_pdf_view(directory_name, file_name):
    """Fetches a PDF from Azure Blob Storage and returns it as an HTTP response for inline display."""
    try:
        blob_path = f"{directory_name}/{file_name}"
        logger.info(f"Fetching PDF from blob path: {blob_path}")

        blob_client = blob_service_client.get_blob_client(container=BLOB_CONTAINER_NAME, blob=blob_path)

        # Download blob content
        download_stream = blob_client.download_blob()
        pdf_bytes = download_stream.readall()
        logger.info(f"PDF '{file_name}' fetched successfully.")

        # Determine content type (for PDF viewer in browser)
        content_type, _ = mimetypes.guess_type(file_name)
        if content_type is None:
            logger.warning(f"Could not determine content type for '{file_name}', defaulting to 'application/octet-stream'.")
            content_type = 'application/octet-stream'

        return content_type, pdf_bytes

    except Exception as e:
        logger.error(f"Error fetching PDF '{file_name}' from '{directory_name}': {e}")
        return None, None