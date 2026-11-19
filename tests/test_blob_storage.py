"""Tests for the blob storage container."""

import unittest
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

from azure.core.exceptions import HttpResponseError, ResourceExistsError

from shinto.blob_storage import BlobStorageContainer
from shinto.exceptions import ShintoSizeLimitException

CONTAINER_ARGS = {
    "account_name": "account",
    "container_name": "container",
    "tenant_id": "tenant",
    "client_id": "client",
    "client_secret": "secret",
}


def _http_error(status: int) -> HttpResponseError:
    error = HttpResponseError(message=f"status {status}")
    error.status_code = status
    return error


@patch("shinto.blob_storage.ClientSecretCredential", MagicMock())
@patch("shinto.blob_storage.SyncClientSecretCredential", MagicMock())
@patch("shinto.blob_storage.ContainerClient", MagicMock())
class TestContainerCreation(unittest.TestCase):
    """Test creating the container when initializing."""

    @patch("shinto.blob_storage.SyncContainerClient")
    def test_creates_container(self, sync_client: MagicMock):
        """Test that the container is created."""
        BlobStorageContainer(**CONTAINER_ARGS)
        sync_client.return_value.create_container.assert_called_once()

    @patch("shinto.blob_storage.SyncContainerClient")
    def test_existing_container(self, sync_client: MagicMock):
        """Test that an existing container is not an error."""
        sync_client.return_value.create_container.side_effect = ResourceExistsError("exists")
        BlobStorageContainer(**CONTAINER_ARGS)

    @patch("shinto.blob_storage.SyncContainerClient")
    def test_no_permission_to_create_container(self, sync_client: MagicMock):
        """Test that missing permission to create the container only logs a warning."""
        sync_client.return_value.create_container.side_effect = _http_error(HTTPStatus.FORBIDDEN)
        with self.assertLogs(level="WARNING") as logs:
            BlobStorageContainer(**CONTAINER_ARGS)
        self.assertIn("Not allowed to create blob container 'container'", logs.output[0])

    @patch("shinto.blob_storage.SyncContainerClient")
    def test_other_create_container_error(self, sync_client: MagicMock):
        """Test that other errors when creating the container are raised."""
        sync_client.return_value.create_container.side_effect = _http_error(
            HTTPStatus.INTERNAL_SERVER_ERROR
        )
        with self.assertRaises(HttpResponseError):
            BlobStorageContainer(**CONTAINER_ARGS)


@patch("shinto.blob_storage.ClientSecretCredential", MagicMock())
@patch("shinto.blob_storage.SyncClientSecretCredential", MagicMock())
@patch("shinto.blob_storage.SyncContainerClient", MagicMock())
@patch("shinto.blob_storage.ContainerClient", MagicMock())
class TestUploadStorageLimit(unittest.IsolatedAsyncioTestCase):
    """Test the storage limit check when uploading."""

    def _container(self) -> BlobStorageContainer:
        container = BlobStorageContainer(**CONTAINER_ARGS, max_storage_size_bytes=100)
        blob_client = MagicMock()
        blob_client.__aenter__ = AsyncMock(return_value=blob_client)
        blob_client.__aexit__ = AsyncMock(return_value=False)
        blob_client.upload_blob = AsyncMock()
        blob_client.get_blob_properties = AsyncMock(return_value=MagicMock(size=10))
        container.container_client = MagicMock()
        container.container_client.get_blob_client.return_value = blob_client
        container.get_total_container_size = AsyncMock(return_value=0)
        return container

    async def test_used_storage_bytes_skips_listing(self):
        """Test that the container is not listed when the used storage is given."""
        container = self._container()
        result = await container.upload_file(b"0123456789", name="a.txt", used_storage_bytes=50)
        container.get_total_container_size.assert_not_awaited()
        self.assertEqual(result["metadata"]["size"], 10)

    async def test_used_storage_bytes_over_limit(self):
        """Test that the limit is enforced with the given used storage."""
        container = self._container()
        with self.assertRaises(ShintoSizeLimitException):
            await container.upload_file(b"0123456789", name="a.txt", used_storage_bytes=95)
        container.container_client.get_blob_client.assert_not_called()

    async def test_lists_container_without_used_storage_bytes(self):
        """Test that the container is listed when the used storage is not given."""
        container = self._container()
        container.get_total_container_size.return_value = 95
        with self.assertRaises(ShintoSizeLimitException):
            await container.upload_file(b"0123456789", name="a.txt")
        container.get_total_container_size.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
