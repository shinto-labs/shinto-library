"""Blob storage utilities for Azure Blob Storage."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from re import match
from typing import Any, BinaryIO

import anyio
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity.aio import ClientSecretCredential
from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import ContainerClient

from shinto.exceptions import ShintoException


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
    file: BinaryIO | bytes | Path | str,
    file_id: str | None = None,
    metadata: dict[str, Any] | str | None = None,
    name: str | None = None,
    content_type: str | None = None,
    content_type_regex: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Upload a file to Azure Blob Storage."""
    if isinstance(file, (str)):
        file = Path(file)
    if isinstance(file, Path):
        if not file.exists():
            raise ValueError(f"File {file} does not exist")
        name = name or file.name

        async with await anyio.open_file(file, "rb") as f:
            file = await f.read()

    if content_type_regex and not match(content_type_regex, content_type):
        raise ValueError(f"File type {content_type} does not match regex {content_type_regex}")

    metadata = metadata or {}
    logging.debug("Uploading file %s with metadata %s", name, metadata)
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
            file,
            metadata={
                "name": name,
                **metadata,
            },
            overwrite=overwrite,
            content_settings=ContentSettings(content_type=content_type),
        )
        logging.debug("File uploaded successfully")
        blob_properties = await blob_client.get_blob_properties()

    return {
        "id": blob_id,
        "metadata": {
            "name": name,
            "type": content_type,
            "size": blob_properties.size,
            **metadata,
        },
    }


async def delete_file(blob_container_client: ContainerClient, file_id: str) -> None:
    """Delete a file from Azure Blob Storage."""
    try:
        async with blob_container_client.get_blob_client(file_id) as blob_client:
            try:
                await blob_client.delete_blob()
            except ResourceExistsError as e:
                if "immutable" in str(e):
                    raise ShintoException(f"File {file_id} is immutable, cannot delete") from e
    except ResourceNotFoundError as e:
        raise ShintoException(f"File {file_id} not found, cannot delete") from e


async def download_file(
    blob_container_client: ContainerClient,
    file_id: str,
) -> dict[str, Any]:
    """Download and return file from Azure Blob Storage."""
    try:
        async with blob_container_client.get_blob_client(file_id) as blob_client:
            blob_download_stream = await blob_client.download_blob()
            blob_content = await blob_download_stream.readall()
    except ResourceNotFoundError as e:
        raise ShintoException(f"File {file_id} not found") from e

    return blob_content
