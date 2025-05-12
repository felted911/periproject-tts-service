# Tests for cache error handling
import os
import pytest
import asyncio
from unittest import mock
from pathlib import Path

from src.tts_service.infrastructure import (
    CacheManager,
    FileStorage,
    MetadataManager,
    CacheIOError,
    CachePermissionError,
    CacheDiskFullError,
    CacheSerializationError,
)


class TestFileStorageErrorHandling:
    """Test file storage error handling."""

    @pytest.mark.asyncio
    async def test_write_permission_error(self, test_cache_dir):
        """Test permission error during write."""
        storage = FileStorage(test_cache_dir)

        # Mock aiofiles.open to raise PermissionError
        with mock.patch("aiofiles.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(CachePermissionError) as excinfo:
                await storage.write("test:key", b"test data")

            # Check error details
            assert "Permission denied" in str(excinfo.value)
            assert "test:key" in str(excinfo.value.details)

    @pytest.mark.asyncio
    async def test_write_disk_full_error(self, test_cache_dir):
        """Test disk full error during write."""
        storage = FileStorage(test_cache_dir)

        # Create OSError with errno 28 (No space left on device)
        disk_full_error = OSError("No space left on device")
        disk_full_error.errno = 28

        # Mock aiofiles.open to raise disk full error
        with mock.patch("aiofiles.open", side_effect=disk_full_error):
            with pytest.raises(CacheDiskFullError) as excinfo:
                await storage.write("test:key", b"test data")

            # Check error details
            assert "Insufficient disk space" in str(excinfo.value)
            assert "test:key" in str(excinfo.value.details)

    @pytest.mark.asyncio
    async def test_write_io_error(self, test_cache_dir):
        """Test I/O error during write."""
        storage = FileStorage(test_cache_dir)

        # Mock aiofiles.open to raise generic OSError
        with mock.patch("aiofiles.open", side_effect=OSError("I/O error")):
            with pytest.raises(CacheIOError) as excinfo:
                await storage.write("test:key", b"test data")

            # Check error details
            assert "I/O error during cache write" in str(excinfo.value)
            assert "test:key" in str(excinfo.value.details)


class TestMetadataManagerErrorHandling:
    """Test metadata manager error handling."""

    @pytest.mark.asyncio
    async def test_save_serialization_error(self, test_cache_dir):
        """Test serialization error during metadata save."""
        metadata_file = Path(test_cache_dir) / "metadata.json"
        manager = MetadataManager(metadata_file, ttl=3600)

        # Create metadata with non-serializable object
        class NonSerializable:
            pass

        manager.metadata = {"key": NonSerializable()}

        with pytest.raises(CacheSerializationError) as excinfo:
            await manager.save()

        # Check error details
        assert "Failed to serialize cache metadata" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_save_permission_error(self, test_cache_dir):
        """Test permission error during metadata save."""
        metadata_file = Path(test_cache_dir) / "metadata.json"
        manager = MetadataManager(metadata_file, ttl=3600)

        # Set valid metadata
        manager.metadata = {"key": {"value": "test"}}

        # Mock aiofiles.open to raise PermissionError
        with mock.patch("aiofiles.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(CachePermissionError) as excinfo:
                await manager.save()

        # Check error details
        assert "Permission denied when saving metadata" in str(excinfo.value)
        assert str(metadata_file.with_suffix(".tmp")) in str(excinfo.value.details["file_path"])

    @pytest.mark.asyncio
    async def test_save_rename_error(self, test_cache_dir):
        """Test error during metadata file rename."""
        metadata_file = Path(test_cache_dir) / "metadata.json"
        manager = MetadataManager(metadata_file, ttl=3600)

        # Set valid metadata
        manager.metadata = {"key": {"value": "test"}}

        # Mock Path.rename to raise OSError
        with mock.patch("pathlib.Path.rename", side_effect=OSError("Rename failed")):
            with pytest.raises(CacheIOError) as excinfo:
                await manager.save()

        # Check error details
        assert "Failed to rename metadata file" in str(excinfo.value)
        assert str(metadata_file) in str(excinfo.value.details["metadata_file"])


class TestCacheManagerErrorHandling:
    """Test cache manager error handling."""

    @pytest.mark.asyncio
    async def test_set_with_write_error(self, test_cache_dir):
        """Test set method with write error."""
        cache = CacheManager(
            cache_dir=test_cache_dir,
            enabled=True,
            ttl=3600,
            max_size=1024 * 1024,
        )

        # Mock FileStorage.write to raise CacheIOError
        with mock.patch.object(
            cache._storage, "write", side_effect=CacheIOError("Test I/O error", {"key": "test:key"})
        ):
            # Set should return False instead of raising the error
            result = await cache.set("test:key", b"test data")
            assert result is False

    @pytest.mark.asyncio
    async def test_set_with_metadata_error(self, test_cache_dir):
        """Test set method with metadata save error."""
        cache = CacheManager(
            cache_dir=test_cache_dir,
            enabled=True,
            ttl=3600,
            max_size=1024 * 1024,
        )

        # Mock MetadataManager.save to raise CacheSerializationError
        with mock.patch.object(
            cache._metadata, "save", side_effect=CacheSerializationError("Test serialization error", {})
        ):
            # Set should return False instead of raising the error
            result = await cache.set("test:key", b"test data")
            assert result is False

            # The data file should be deleted since metadata save failed
            file_path = await cache._storage.get_file_path("test:key")
            assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_set_with_disk_full_recovery(self, test_cache_dir):
        """Test set method with disk full error and recovery."""
        cache = CacheManager(
            cache_dir=test_cache_dir,
            enabled=True,
            ttl=3600,
            max_size=1024 * 1024,
        )

        # Add some data to the cache first
        await cache.set("key1", b"data1" * 100)
        await cache.set("key2", b"data2" * 100)

        # Mock counter to track call count
        call_counter = {"count": 0}

        # Create a side effect function that raises error first time, succeeds second time
        async def write_side_effect(key, data):
            if call_counter["count"] == 0:
                call_counter["count"] += 1
                disk_full_error = OSError("No space left on device")
                disk_full_error.errno = 28
                raise CacheDiskFullError("Disk full", {"key": key})
            else:
                # Original implementation - actually write the file
                file_path = await cache._storage.get_file_path(key)
                # Create parent directory if it doesn't exist
                file_path.parent.mkdir(parents=True, exist_ok=True)
                # Make sure the file exists
                file_path.touch(exist_ok=True)
                return True

        # Mock FileStorage.write to use our side effect function
        with mock.patch.object(cache._storage, "write", side_effect=write_side_effect):
            # Create a simplified force eviction method that just records it was called
            original_force_eviction = cache._force_eviction
            force_eviction_called = [False]

            async def mock_force_eviction(required_space):
                force_eviction_called[0] = True
                # Just to ensure the test passes
                return await original_force_eviction(required_space)

            with mock.patch.object(cache, "_force_eviction", side_effect=mock_force_eviction):
                # Set should return True after recovery
                result = await cache.set("test:key", b"test data")

                # Verify that force_eviction was called
                assert force_eviction_called[0] is True
                # With the fixed implementation, this should now pass
                assert result is True

    @pytest.mark.asyncio
    async def test_force_eviction(self, test_cache_dir):
        """Test force eviction method."""
        # Create a simplistic test without complex mocking
        cache = CacheManager(
            cache_dir=test_cache_dir,
            enabled=True,
            ttl=3600,
            max_size=1024 * 1024,
        )

        # Create the test data
        data1 = b"data1" * 100  # 500 bytes
        data2 = b"data2" * 100  # 500 bytes

        # Mock the storage methods for tracking
        deleted_keys = []

        # Simple mock implementations that track operations
        async def mock_write(key, data):
            return True

        async def mock_delete(key):
            deleted_keys.append(key)
            return True

        async def mock_read(key):
            if key == "key1" and "key1" in deleted_keys:
                return None
            elif key == "key1":
                return data1
            elif key == "key2":
                return data2
            return None

        # Apply the mocks
        with mock.patch.object(cache._storage, "write", side_effect=mock_write):
            with mock.patch.object(cache._storage, "delete", side_effect=mock_delete):
                with mock.patch.object(cache._storage, "read", side_effect=mock_read):
                    # Setup the metadata directly
                    cache._metadata.metadata = {
                        "key1": {
                            "file_name": "key1",
                            "size": len(data1),
                            "last_accessed": 1000,  # Older timestamp
                            "created": 1000,
                        },
                        "key2": {
                            "file_name": "key2",
                            "size": len(data2),
                            "last_accessed": 2000,  # Newer timestamp
                            "created": 2000,
                        },
                    }

                    # Force eviction - should evict key1 but not key2
                    await cache._force_eviction(500)

                    # Check which keys were deleted
                    assert "key1" in deleted_keys
                    assert "key2" not in deleted_keys
