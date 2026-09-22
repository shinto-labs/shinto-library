"""Blob storage utilities for Azure Blob Storage."""

from __future__ import annotations

import contextlib
import json
import logging
import os
import uuid
from pathlib import Path
from re import match
from typing import Any, BinaryIO

import anyio
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity import ClientSecretCredential as SyncClientSecretCredential
from azure.identity.aio import ClientSecretCredential
from azure.storage.blob import ContainerClient as SyncContainerClient
from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import ContainerClient

from shinto.exceptions import (
    ShintoBadInputException,
    ShintoException,
    ShintoNotFoundException,
    ShintoSizeLimitException,
)


def _get_file_size(file: BinaryIO | bytes) -> int:
    """Return the size of a file without reading the entire file into memory."""
    if isinstance(file, bytes):
        return len(file)

    return os.fstat(file.fileno()).st_size


class BlobStorageContainer:
    """Class representing a blob storage container with size limits."""

    container_client: ContainerClient
    max_upload_size_bytes: int
    max_storage_size_bytes: int

    def __init__(
        self,
        account_name: str,
        container_name: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        max_upload_size_bytes: int | None = None,
        max_storage_size_bytes: int | None = None,
    ):
        """Initialize the blob storage container with size limits."""
        container_client = ContainerClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            container_name=container_name,
            credential=ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            ),
        )
        with contextlib.suppress(ResourceExistsError):
            SyncContainerClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                container_name=container_name,
                credential=SyncClientSecretCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                ),
            ).create_container()

        self.container_client = container_client
        self.max_upload_size_bytes = max_upload_size_bytes or 4 * 1024**3
        self.max_storage_size_bytes = max_storage_size_bytes or 100 * 1024**3

    def get_container_client(self) -> ContainerClient:
        """Return the container client."""
        return self.container_client

    async def get_total_container_size(self) -> int:
        """Calculate the total size of blobs in the container."""
        total_size = 0

        async for blob in self.container_client.list_blobs():
            total_size += blob.size or 0

        return total_size

    async def upload_file(
        self,
        file: BinaryIO | bytes | Path | str,
        file_id: str | None = None,
        metadata: dict[str, Any] | str | None = None,
        name: str | None = None,
        content_type: str | None = None,
        content_type_regex: str | None = None,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Upload a file to Azure Blob Storage."""
        blob_id = file_id or str(uuid.uuid4())

        if isinstance(file, str):
            file = Path(file)
        if isinstance(file, Path):
            if not file.exists():
                raise ShintoBadInputException(f"File {file} does not exist")
            name = name or file.name

            async with await anyio.open_file(file, "rb") as f:
                file = await f.read()
        file_size = _get_file_size(file)
        if file_size > self.max_upload_size_bytes:
            raise ShintoSizeLimitException(
                f"File size {file_size:,} bytes exceeds the "
                f"upload size limit of {self.max_upload_size_bytes:,} bytes"
            )
        container_size = await self.get_total_container_size()
        if container_size + file_size > self.max_storage_size_bytes:
            raise ShintoSizeLimitException(
                f"Uploading this file would exceed the blob storage "
                f"size limit of {self.max_storage_size_bytes:,} bytes"
            )

        if content_type_regex and (not content_type or not match(content_type_regex, content_type)):
            raise ShintoBadInputException(
                f"File type {content_type} does not match regex {content_type_regex}"
            )

        metadata = metadata or {}
        logging.debug("Uploading file %s with metadata %s", name, metadata)
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError as e:
                raise ShintoBadInputException(f"Metadata string is not valid JSON: {e}") from e
        if metadata and not isinstance(metadata, dict):
            raise ShintoBadInputException(
                "Metadata must be a valid dictionary or a JSON string representing a dictionary"
            )

        async with self.container_client.get_blob_client(blob_id) as blob_client:
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

    async def get_file_metadata(
        self,
        file_id: str,
    ) -> dict[str, Any]:
        """Retrieve metadata for a file from Azure Blob Storage."""
        try:
            async with self.container_client.get_blob_client(file_id) as blob_client:
                blob_properties = await blob_client.get_blob_properties()
        except ResourceNotFoundError as e:
            raise ShintoNotFoundException(f"File {file_id} not found") from e

        return {
            "id": file_id,
            "metadata": {
                "name": blob_properties.metadata.get("name"),
                "type": blob_properties.content_settings.content_type,
                "size": blob_properties.size,
                **blob_properties.metadata,
            },
        }

    async def update_file_metadata(
        self,
        file_id: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Update metadata for a file in Azure Blob Storage."""
        try:
            async with self.container_client.get_blob_client(file_id) as blob_client:
                blob_properties = await blob_client.get_blob_properties()
                current_metadata = blob_properties.metadata
                current_metadata.update(metadata)
                await blob_client.set_blob_metadata(current_metadata)
        except ResourceNotFoundError as e:
            raise ShintoNotFoundException(f"File {file_id} not found") from e

        return {
            "id": file_id,
            "metadata": {
                "name": current_metadata.get("name"),
                "type": blob_properties.content_settings.content_type,
                "size": blob_properties.size,
                **current_metadata,
            },
        }

    async def delete_file(self, file_id: str) -> None:
        """Delete a file from Azure Blob Storage."""
        try:
            async with self.container_client.get_blob_client(file_id) as blob_client:
                try:
                    await blob_client.delete_blob()
                except ResourceExistsError as e:
                    if "immutable" in str(e):
                        raise ShintoException(f"File {file_id} is immutable, cannot delete") from e
        except ResourceNotFoundError as e:
            raise ShintoNotFoundException(f"File {file_id} not found, cannot delete") from e

    async def download_file(
        self,
        file_id: str,
    ) -> dict[str, Any]:
        """Download and return file from Azure Blob Storage."""
        try:
            async with self.container_client.get_blob_client(file_id) as blob_client:
                blob_download_stream = await blob_client.download_blob()
                blob_content = await blob_download_stream.readall()
        except ResourceNotFoundError as e:
            raise ShintoNotFoundException(f"File {file_id} not found") from e

        return blob_content
