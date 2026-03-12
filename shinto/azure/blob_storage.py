"""Library for data imports."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings

from .general import get_mimetype_for_file


def clear_blob_storage_container(container_client: ContainerClient):
    """Clear blob storage container."""
    try:
        blobs = container_client.list_blobs()
        for blob in blobs:
            container_client.delete_blob(blob.name)
            logging.info(
                "Deleted blob '%s' from container '%s'.", blob.name, container_client.container_name
            )
    except ResourceNotFoundError:
        logging.info("Container '%s' does not exist.", container_client.container_name)


def create_blob_storage_container(
    blob_service_client: BlobServiceClient, container_name: str
) -> ContainerClient:
    """Create blob storage container."""
    try:
        container_client = blob_service_client.create_container(container_name)
        logging.info("Container '%s' created.", container_name)
    except ResourceExistsError:
        container_client = blob_service_client.get_container_client(container_name)
        logging.info("Container '%s' already exists.", container_name)
    return container_client


def get_blob_storage_container_client(
        account_name: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        container_name: str,
    ) -> ContainerClient:
        """get_blob_storage_container_client."""

        container_client = create_blob_storage_container(
            BlobServiceClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                credential=ClientSecretCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                )
            ),
            container_name
        )

        clear_blob_storage_container(container_client)

        return container_client

def upload_to_blob_storage(container_client: ContainerClient, file_path: str) -> dict:
    """Upload a file to Azure Blob Storage and return a file dict with metadata."""
    file_type = get_mimetype_for_file(file_path)
    file_name = file_path.split("/")[-1]
    blob_id = str(uuid.uuid4())

    with Path(file_path).open("rb") as data:
        file_data = data.read()

    blob_client = container_client.get_blob_client(blob=blob_id)

    blob_client.upload_blob(
        file_data,
        metadata={
            "original_filename": file_name,
        },
        overwrite=False,
        content_settings=ContentSettings(content_type=file_type),
    )
    logging.info("File uploaded successfully to blob storage: %s", file_name)
    blob_properties = blob_client.get_blob_properties()
    blob_size = blob_properties.size

    return {
        "id": blob_id,
        "data": {
            "name": file_name,
            "size": blob_size,
            "type": file_type,
        },
    }
