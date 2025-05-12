"""Tests for metadata manager functionality."""

import pytest
import asyncio
import tempfile
import shutil
import os
import json
import time
from pathlib import Path
from unittest import mock

from tts_service.infrastructure.cache.metadata_manager import MetadataManager
from tts_service.infrastructure.exceptions import (
    CacheIOError,
    CachePermissionError,
    CacheDiskFullError,
    CacheSerializationError,
)


@pytest.fixture
def temp_metadata_file():
    """Create a temporary directory and metadata file for testing."""
    temp_dir = tempfile.mkdtemp()
    metadata_file = Path(temp_dir) / "metadata.json"
    yield metadata_file
    shutil.rmtree(temp_dir)


class AsyncContextManagerMock:
    def __init__(self, return_value=None, exception=None):
        self.return_value = return_value
        self.exception = exception

    async def __aenter__(self):
        if self.exception:
            raise self.exception
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class AsyncFileMock:
    def __init__(self, content=""):
        self.content = content

    async def read(self):
        return self.content

    async def write(self, data):
        self.content = data


@pytest.mark.asyncio
async def test_metadata_manager_set_get(temp_metadata_file):
    """Test setting and getting metadata."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Set metadata
    key = "test_key"
    file_name = "test_file.bin"
    size = 1024
    custom_metadata = {"content_type": "audio/wav"}

    manager.set_metadata(key, file_name, size, custom_metadata)

    # Get metadata
    metadata = manager.get_metadata(key)

    # Verify metadata
    assert metadata is not None
    assert metadata["file_name"] == file_name
    assert metadata["size"] == size
    assert metadata["meta"] == custom_metadata
    assert "created_at" in metadata
    assert "last_accessed" in metadata
    assert "expires_at" in metadata


@pytest.mark.asyncio
async def test_metadata_manager_delete(temp_metadata_file):
    """Test deleting metadata."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Set metadata
    key = "test_key"
    file_name = "test_file.bin"
    size = 1024

    manager.set_metadata(key, file_name, size)

    # Delete metadata
    delete_result = manager.delete_metadata(key)

    # Verify delete result
    assert delete_result is True

    # Try to get deleted metadata
    metadata = manager.get_metadata(key)

    # Verify metadata is None
    assert metadata is None


@pytest.mark.asyncio
async def test_metadata_manager_clear(temp_metadata_file):
    """Test clearing all metadata."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Set multiple metadata entries
    manager.set_metadata("key1", "file1.bin", 1024)
    manager.set_metadata("key2", "file2.bin", 2048)

    # Verify metadata count
    assert manager.get_metadata_count() == 2

    # Clear metadata
    manager.clear_metadata()

    # Verify metadata is cleared
    assert manager.get_metadata_count() == 0
    assert manager.get_metadata("key1") is None
    assert manager.get_metadata("key2") is None


@pytest.mark.asyncio
async def test_metadata_manager_update_access_time(temp_metadata_file):
    """Test updating access time."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Set metadata
    key = "test_key"
    file_name = "test_file.bin"
    size = 1024

    # Mock time.time to return controlled values
    with mock.patch("time.time", side_effect=[1000, 1100]):
        # Set metadata with time = 1000
        manager.set_metadata(key, file_name, size)
        initial_access_time = manager.get_metadata(key)["last_accessed"]

        # Update access time with time = 1100
        manager.update_access_time(key)
        updated_access_time = manager.get_metadata(key)["last_accessed"]

    # Verify access time was updated
    assert updated_access_time > initial_access_time
    assert updated_access_time == 1100


@pytest.mark.asyncio
async def test_metadata_manager_is_expired(temp_metadata_file):
    """Test checking if metadata is expired."""
    # Create metadata manager with short TTL
    ttl = 100  # 100 second TTL
    manager = MetadataManager(temp_metadata_file, ttl)

    # Set metadata with time = 1000
    with mock.patch("time.time", return_value=1000):
        key = "test_key"
        file_name = "test_file.bin"
        size = 1024
        manager.set_metadata(key, file_name, size)

    # Verify not expired with time = 1000
    with mock.patch("time.time", return_value=1000):
        assert manager.is_expired(key) is False

    # Verify expired with time = 1200
    with mock.patch("time.time", return_value=1200):
        assert manager.is_expired(key) is True


@pytest.mark.asyncio
async def test_metadata_manager_get_all_keys(temp_metadata_file):
    """Test getting all keys."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Set multiple metadata entries
    manager.set_metadata("key1", "file1.bin", 1024)
    manager.set_metadata("key2", "file2.bin", 2048)
    manager.set_metadata("key3", "file3.bin", 3072)

    # Get all keys
    keys = manager.get_all_keys()

    # Verify keys
    assert len(keys) == 3
    assert "key1" in keys
    assert "key2" in keys
    assert "key3" in keys


@pytest.mark.asyncio
async def test_metadata_manager_get_metadata_size(temp_metadata_file):
    """Test getting total metadata size."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Set multiple metadata entries
    manager.set_metadata("key1", "file1.bin", 1024)
    manager.set_metadata("key2", "file2.bin", 2048)

    # Get total size
    total_size = manager.get_metadata_size()

    # Verify total size
    assert total_size == 3072  # 1024 + 2048


@pytest.mark.asyncio
async def test_metadata_manager_save_load(temp_metadata_file):
    """Test saving and loading metadata."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Set multiple metadata entries
    manager.set_metadata("key1", "file1.bin", 1024, {"type": "audio"})
    manager.set_metadata("key2", "file2.bin", 2048, {"type": "video"})

    # Mock aiofiles.open for save
    file_mock = AsyncFileMock()
    context_mock = AsyncContextManagerMock(file_mock)

    # Mock the rename operation as well
    original_rename = Path.rename

    def mock_rename(self, target):
        # Instead of renaming, just create the target file with the same content
        # This simulates a successful rename operation
        with open(target, "w") as f:
            f.write(file_mock.content)
        return target

    with mock.patch("aiofiles.open", return_value=context_mock), mock.patch("pathlib.Path.rename", mock_rename):
        # Save metadata
        await manager.save()

        # Get the JSON content that would have been saved
        saved_content = file_mock.content

    # Now create a new metadata file with the saved content
    os.makedirs(temp_metadata_file.parent, exist_ok=True)
    with open(temp_metadata_file, "w") as f:
        f.write(saved_content)

    # Create new metadata manager instance
    new_manager = MetadataManager(temp_metadata_file, ttl)

    # Load metadata
    await new_manager.load()

    # Verify loaded metadata
    assert new_manager.get_metadata_count() == 2
    assert new_manager.get_metadata("key1")["size"] == 1024
    assert new_manager.get_metadata("key1")["meta"]["type"] == "audio"
    assert new_manager.get_metadata("key2")["size"] == 2048
    assert new_manager.get_metadata("key2")["meta"]["type"] == "video"


@pytest.mark.asyncio
async def test_metadata_manager_load_nonexistent_file(temp_metadata_file):
    """Test loading metadata from nonexistent file."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Load metadata (file doesn't exist yet)
    await manager.load()

    # Verify empty metadata
    assert manager.get_metadata_count() == 0


@pytest.mark.asyncio
async def test_metadata_manager_clean_expired_items(temp_metadata_file):
    """Test cleaning expired items during load."""
    # Create metadata manager with short TTL
    ttl = 100  # 100 second TTL
    manager = MetadataManager(temp_metadata_file, ttl)

    # Mock time.time to return controlled value for setup
    with mock.patch("time.time", return_value=1000):
        # Set metadata with custom expiration times
        manager.metadata = {
            "expired_key": {
                "file_name": "expired.bin",
                "size": 1024,
                "created_at": 800,
                "last_accessed": 900,
                "expires_at": 950,  # Already expired
                "meta": {},
            },
            "valid_key": {
                "file_name": "valid.bin",
                "size": 2048,
                "created_at": 900,
                "last_accessed": 950,
                "expires_at": 1100,  # Not expired
                "meta": {},
            },
        }

    # Save metadata to a file
    with open(temp_metadata_file, "w") as f:
        json.dump(manager.metadata, f)

    # Create new metadata manager
    new_manager = MetadataManager(temp_metadata_file, ttl)

    # Load metadata with time still at 1000
    with mock.patch("time.time", return_value=1000):
        await new_manager.load()

    # Verify expired item was removed
    assert new_manager.get_metadata("expired_key") is None
    assert new_manager.get_metadata("valid_key") is not None


@pytest.mark.asyncio
async def test_metadata_manager_save_permission_error(temp_metadata_file):
    """Test saving metadata with permission error."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Set metadata
    manager.set_metadata("key1", "file1.bin", 1024)

    # Mock aiofiles.open to raise PermissionError
    context_mock = AsyncContextManagerMock(exception=PermissionError("Mock permission error"))

    with mock.patch("aiofiles.open", return_value=context_mock):
        # Save metadata with permission error
        with pytest.raises(CachePermissionError):
            await manager.save()


@pytest.mark.asyncio
async def test_metadata_manager_save_disk_full(temp_metadata_file):
    """Test saving metadata with disk full error."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Set metadata
    manager.set_metadata("key1", "file1.bin", 1024)

    # Create a disk full error
    error = OSError("Mock disk full error")
    error.errno = 28

    # Mock aiofiles.open to raise OSError with errno 28
    context_mock = AsyncContextManagerMock(exception=error)

    with mock.patch("aiofiles.open", return_value=context_mock):
        # Save metadata with disk full error
        with pytest.raises(CacheDiskFullError):
            await manager.save()


class UnserializableObject:
    """An object that can't be serialized to JSON."""

    pass


@pytest.mark.asyncio
async def test_metadata_manager_save_serialization_error(temp_metadata_file):
    """Test saving metadata with serialization error."""
    # Create metadata manager
    ttl = 3600
    manager = MetadataManager(temp_metadata_file, ttl)

    # Create metadata with unserializable object
    manager.metadata = {
        "key1": {
            "file_name": "file1.bin",
            "size": 1024,
            "created_at": 1000,
            "last_accessed": 1000,
            "expires_at": 2000,
            "meta": {"unserializable": UnserializableObject()},  # Can't be serialized
        }
    }

    # Save metadata with serialization error
    with pytest.raises(CacheSerializationError):
        await manager.save()
