"""Blob storage utilities for Azure Blob Storage."""

from __future__ import annotations

import json
import logging
import uuid
from re import match
from typing import Any, BinaryIO, Protocol

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity.aio import ClientSecretCredential
from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import ContainerClient

from shinto.exceptions import ShintoException


class UploadFileLike(Protocol):
    """Protocol for uploaded file objects used by upload_file."""

    filename: str
    content_type: str
    file: BinaryIO


def setup_blob_container_client(
    account_name: str, container_name: str, tenant_id: str, client_id: str, client_secret: str
) -> ContainerClient:
    """Set up a blob container client."""
    return ContainerClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        container_name=container_name,
        credential=ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        ),
    )


async def upload_file(
    blob_container_client: ContainerClient,
    file: UploadFileLike,
    file_metadata: dict[str, Any] | str | None = None,
    file_id: str | None = None,
    file_type_regex: str | None = None,
) -> dict[str, Any]:
    """Upload a file to Azure Blob Storage."""
    if file_type_regex and not match(file_type_regex, file.content_type):
        raise ValueError(f"File type {file.content_type} does not match regex {file_type_regex}")
    metadata = file_metadata or {}
    logging.debug("Uploading file %s with metadata %s", file.filename, metadata)
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError as e:
            raise ValueError(f"Metadata string is not valid JSON: {e}") from e
    if metadata and not isinstance(metadata, dict):
        raise ValueError(
            "Metadata must be a valid dictionary or a JSON string representing a dictionary"
        )

    blob_id = file_id or str(uuid.uuid4())
    async with blob_container_client.get_blob_client(blob_id) as blob_client:
        await blob_client.upload_blob(
            file.file,
            metadata={
                "original_filename": file.filename,
                **metadata,
            },
            overwrite=False,
            content_settings=ContentSettings(content_type=file.content_type),
        )
        logging.info("File uploaded successfully")
        blob_properties = await blob_client.get_blob_properties()
        blob_size = blob_properties.size

    return {
        "id": blob_id,
        "metadata": {
            "name": file.filename,
            "size": blob_size,
            "type": file.content_type,
            **metadata,
        },
    }


async def delete_file(blob_container_client: ContainerClient, blob_id: str) -> None:
    """Delete a file from Azure Blob Storage."""
    try:
        async with blob_container_client.get_blob_client(blob_id) as blob_client:
            try:
                await blob_client.delete_blob()
            except ResourceExistsError as e:
                if "immutable" in str(e):
                    raise ShintoException(f"Blob {blob_id} is immutable, cannot delete") from e
    except ResourceNotFoundError as e:
        raise ShintoException(f"Blob {blob_id} not found, cannot delete") from e


async def download_file(
    blob_container_client: ContainerClient,
    blob_id: str,
) -> dict[str, Any]:
    """Download and return file from Azure Blob Storage."""
    try:
        async with blob_container_client.get_blob_client(blob_id) as blob_client:
            blob_properties = await blob_client.get_blob_properties()
            blob_download_stream = await blob_client.download_blob()
            blob_content = await blob_download_stream.readall()
    except ResourceNotFoundError as e:
        raise ShintoException(f"Blob {blob_id} not found") from e

    filename = blob_properties.metadata.get("original_filename", blob_id)
    return {
        "blob_content": blob_content,
        "content_type": blob_properties.content_settings.content_type,
        "filename": filename,
    }
