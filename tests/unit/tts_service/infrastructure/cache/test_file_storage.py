"""Tests for file storage functionality."""

import pytest
import asyncio
import tempfile
import shutil
import os
from pathlib import Path
from unittest import mock

from tts_service.infrastructure.cache.file_storage import FileStorage
from tts_service.infrastructure.exceptions import (
    CacheIOError, CachePermissionError, CacheDiskFullError
)


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
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
    def __init__(self, content=None):
        self.content = content or b""
        
    async def read(self):
        return self.content
        
    async def write(self, data):
        self.content = data


@pytest.mark.asyncio
async def test_file_storage_write_read(temp_cache_dir):
    """Test writing and reading data with file storage."""
    # Create file storage
    storage = FileStorage(temp_cache_dir)
    
    # Test data
    test_key = "test_key"
    test_data = b"test_data"
    
    # Write data
    write_result = await storage.write(test_key, test_data)
    
    # Verify write result
    assert write_result is True
    
    # Get file path
    file_path = await storage.get_file_path(test_key)
    
    # Verify file exists
    assert file_path.exists()
    
    # Read data
    read_data = await storage.read(test_key)
    
    # Verify read data
    assert read_data == test_data


@pytest.mark.asyncio
async def test_file_storage_delete(temp_cache_dir):
    """Test deleting data with file storage."""
    # Create file storage
    storage = FileStorage(temp_cache_dir)
    
    # Test data
    test_key = "test_key"
    test_data = b"test_data"
    
    # Write data
    await storage.write(test_key, test_data)
    
    # Delete data
    delete_result = await storage.delete(test_key)
    
    # Verify delete result
    assert delete_result is True
    
    # Get file path
    file_path = await storage.get_file_path(test_key)
    
    # Verify file does not exist
    assert not file_path.exists()
    
    # Try to read deleted data
    read_data = await storage.read(test_key)
    
    # Verify read result is None
    assert read_data is None


@pytest.mark.asyncio
async def test_file_storage_clear(temp_cache_dir):
    """Test clearing all data with file storage."""
    # Create file storage
    storage = FileStorage(temp_cache_dir)
    
    # Write multiple test files
    await storage.write("key1", b"data1")
    await storage.write("key2", b"data2")
    
    # Clear all data
    clear_result = await storage.clear()
    
    # Verify clear result
    assert clear_result is True
    
    # Verify files are deleted
    file_path1 = await storage.get_file_path("key1")
    file_path2 = await storage.get_file_path("key2")
    assert not file_path1.exists()
    assert not file_path2.exists()


@pytest.mark.asyncio
async def test_file_storage_read_nonexistent(temp_cache_dir):
    """Test reading nonexistent data with file storage."""
    # Create file storage
    storage = FileStorage(temp_cache_dir)
    
    # Read nonexistent data
    read_data = await storage.read("nonexistent_key")
    
    # Verify read result is None
    assert read_data is None


@pytest.mark.asyncio
async def test_file_storage_read_permission_error(temp_cache_dir):
    """Test reading data with permission error."""
    # Create file storage
    storage = FileStorage(temp_cache_dir)
    
    # Test data
    test_key = "test_key"
    test_data = b"test_data"
    
    # Write data
    await storage.write(test_key, test_data)
    
    # Mock aiofiles.open to raise PermissionError
    async_mock = mock.Mock()
    async_mock.__aenter__ = mock.AsyncMock(side_effect=PermissionError("Mock permission error"))
    async_mock.__aexit__ = mock.AsyncMock(return_value=None)
    
    with mock.patch('aiofiles.open', return_value=async_mock):
        # Read data with permission error
        with pytest.raises(CachePermissionError):
            await storage.read(test_key)


@pytest.mark.asyncio
async def test_file_storage_write_io_error(temp_cache_dir):
    """Test writing data with I/O error."""
    # Create file storage
    storage = FileStorage(temp_cache_dir)
    
    # Mock aiofiles.open to raise OSError
    async_mock = mock.Mock()
    async_mock.__aenter__ = mock.AsyncMock(side_effect=OSError("Mock I/O error"))
    async_mock.__aexit__ = mock.AsyncMock(return_value=None)
    
    with mock.patch('aiofiles.open', return_value=async_mock):
        # Write data with I/O error
        with pytest.raises(CacheIOError):
            await storage.write("test_key", b"test_data")


@pytest.mark.asyncio
async def test_file_storage_write_disk_full(temp_cache_dir):
    """Test writing data with disk full error."""
    # Create file storage
    storage = FileStorage(temp_cache_dir)
    
    # Create a disk full error
    error = OSError("Mock disk full error")
    error.errno = 28
    
    # Mock aiofiles.open to raise OSError with errno 28
    async_mock = mock.Mock()
    async_mock.__aenter__ = mock.AsyncMock(side_effect=error)
    async_mock.__aexit__ = mock.AsyncMock(return_value=None)
    
    with mock.patch('aiofiles.open', return_value=async_mock):
        # Write data with disk full error
        with pytest.raises(CacheDiskFullError):
            await storage.write("test_key", b"test_data")
