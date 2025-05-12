"""File storage implementation for cache data."""

import hashlib
from pathlib import Path
import aiofiles
from typing import Optional

from ..logging import get_logger
from ..exceptions import CacheIOError, CachePermissionError, CacheDiskFullError, CacheError
from .protocols import CacheStorageProtocol

logger = get_logger(__name__)


class FileStorage:
    """File storage implementation for cache data."""

    def __init__(self, cache_dir: str):
        """Initialize file storage.

        Args:
            cache_dir: Directory to store cached files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    async def get_file_path(self, key: str) -> Path:
        """Get file path for a cache key.

        Args:
            key: Cache key

        Returns:
            Path to the file
        """
        # Generate file name from key
        file_name = f"{hashlib.md5(key.encode()).hexdigest()}.bin"
        return self.cache_dir / file_name

    async def read(self, key: str) -> Optional[bytes]:
        """Read data from cache storage.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found

        Raises:
            CacheIOError: If there's an I/O error reading the file
            CachePermissionError: If there's a permission error accessing the file
        """
        try:
            file_path = await self.get_file_path(key)

            # Check if file exists
            if not file_path.exists():
                return None

            # Read file
            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()

            return data

        except PermissionError as e:
            logger.error(f"Cache read permission error: {str(e)}")
            raise CachePermissionError(
                f"Permission denied when reading from cache: {str(e)}", {"key": key, "file_path": str(file_path)}
            ) from e
        except OSError as e:
            logger.error(f"Cache read I/O error: {str(e)}")
            raise CacheIOError(
                f"I/O error during cache read: {str(e)}", {"key": key, "file_path": str(file_path)}
            ) from e
        except Exception as e:
            logger.exception(f"Unexpected cache read error: {str(e)}")
            raise CacheError(f"Unexpected error during cache read: {str(e)}", {"key": key}) from e

    async def write(self, key: str, data: bytes) -> bool:
        """Write data to cache storage.

        Args:
            key: Cache key
            data: Data to write

        Returns:
            True if successful, False otherwise

        Raises:
            CacheIOError: When file I/O operations fail
            CachePermissionError: When permission issues occur
            CacheDiskFullError: When disk space is insufficient
        """
        file_path = None
        try:
            file_path = await self.get_file_path(key)

            # Write data to file
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(data)

            return True

        except PermissionError as e:
            logger.error(f"Cache write permission error: {str(e)}")
            raise CachePermissionError(
                f"Permission denied when writing to cache: {str(e)}",
                {"key": key, "file_path": str(file_path) if file_path else "unknown"},
            ) from e
        except OSError as e:
            # OSError with errno 28 is "No space left on device"
            if hasattr(e, "errno") and e.errno == 28:
                logger.error(f"Cache write disk full error: {str(e)}")
                raise CacheDiskFullError(
                    f"Insufficient disk space for cache write: {str(e)}",
                    {"key": key, "file_path": str(file_path) if file_path else "unknown"},
                ) from e
            else:
                logger.error(f"Cache write I/O error: {str(e)}")
                raise CacheIOError(
                    f"I/O error during cache write: {str(e)}",
                    {"key": key, "file_path": str(file_path) if file_path else "unknown"},
                ) from e
        except Exception as e:
            logger.exception(f"Unexpected cache write error: {str(e)}")
            raise CacheError(f"Unexpected error during cache write: {str(e)}", {"key": key}) from e

    async def delete(self, key: str) -> bool:
        """Delete data from cache storage.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise

        Raises:
            CacheIOError: When file I/O operations fail
            CachePermissionError: When permission issues occur
        """
        try:
            file_path = await self.get_file_path(key)

            # Delete file if it exists
            if file_path.exists():
                file_path.unlink()

            return True

        except PermissionError as e:
            logger.error(f"Cache delete permission error: {str(e)}")
            raise CachePermissionError(
                f"Permission denied when deleting from cache: {str(e)}", {"key": key, "file_path": str(file_path)}
            ) from e
        except OSError as e:
            logger.error(f"Cache delete I/O error: {str(e)}")
            raise CacheIOError(
                f"I/O error during cache delete: {str(e)}", {"key": key, "file_path": str(file_path)}
            ) from e
        except Exception as e:
            logger.exception(f"Unexpected cache delete error: {str(e)}")
            raise CacheError(f"Unexpected error during cache delete: {str(e)}", {"key": key}) from e

    async def clear(self) -> bool:
        """Clear all data from cache storage.

        Returns:
            True if successful, False otherwise

        Raises:
            CacheIOError: When file I/O operations fail
            CachePermissionError: When permission issues occur
        """
        try:
            # Delete all bin files in cache directory
            for file_path in self.cache_dir.glob("*.bin"):
                file_path.unlink()

            return True

        except PermissionError as e:
            logger.error(f"Cache clear permission error: {str(e)}")
            raise CachePermissionError(
                f"Permission denied when clearing cache: {str(e)}", {"cache_dir": str(self.cache_dir)}
            ) from e
        except OSError as e:
            logger.error(f"Cache clear I/O error: {str(e)}")
            raise CacheIOError(f"I/O error during cache clear: {str(e)}", {"cache_dir": str(self.cache_dir)}) from e
        except Exception as e:
            logger.exception(f"Unexpected cache clear error: {str(e)}")
            raise CacheError(
                f"Unexpected error during cache clear: {str(e)}", {"cache_dir": str(self.cache_dir)}
            ) from e
