"""Azure module with helper functions for Azure."""

__all__ = [
    "get_blob_storage_container_client",
    "upload_to_blob_storage"
]

from blob_storage import get_blob_storage_container_client, upload_to_blob_storage
