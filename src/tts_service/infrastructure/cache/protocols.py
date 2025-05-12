"""Protocol definitions for cache-related interfaces."""

from pathlib import Path
from typing import Dict, Any, Optional, List, Protocol, runtime_checkable


@runtime_checkable
class CacheStorageProtocol(Protocol):
    """Protocol for cache storage operations."""

    async def read(self, key: str) -> Optional[bytes]:
        """Read data from cache storage.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found
        """
        ...

    async def write(self, key: str, data: bytes) -> bool:
        """Write data to cache storage.

        Args:
            key: Cache key
            data: Data to write

        Returns:
            True if successful, False otherwise
        """
        ...

    async def delete(self, key: str) -> bool:
        """Delete data from cache storage.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        ...

    async def get_file_path(self, key: str) -> Path:
        """Get file path for a cache key.

        Args:
            key: Cache key

        Returns:
            Path to the file
        """
        ...

    async def clear(self) -> bool:
        """Clear all data from cache storage.

        Returns:
            True if successful, False otherwise
        """
        ...


@runtime_checkable
class CacheMetadataProtocol(Protocol):
    """Protocol for cache metadata operations."""

    async def load(self) -> None:
        """Load metadata from storage."""
        ...

    async def save(self) -> None:
        """Save metadata to storage."""
        ...

    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for cache item.

        Args:
            key: Cache key

        Returns:
            Metadata or None if not found
        """
        ...

    def set_metadata(
        self, key: str, file_name: str, size: int, custom_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set metadata for cache item.

        Args:
            key: Cache key
            file_name: Name of cache file
            size: Size of cached data in bytes
            custom_metadata: Additional metadata
        """
        ...

    def delete_metadata(self, key: str) -> bool:
        """Delete metadata for cache item.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        ...

    def clear_metadata(self) -> None:
        """Clear all metadata."""
        ...

    def update_access_time(self, key: str) -> None:
        """Update last accessed time for cache item.

        Args:
            key: Cache key
        """
        ...

    def is_expired(self, key: str) -> bool:
        """Check if cache item is expired.

        Args:
            key: Cache key

        Returns:
            True if expired, False otherwise
        """
        ...

    def get_all_keys(self) -> List[str]:
        """Get all cache keys.

        Returns:
            List of cache keys
        """
        ...

    def get_metadata_size(self) -> int:
        """Get total size of cached items in bytes.

        Returns:
            Total size in bytes
        """
        ...

    def get_metadata_count(self) -> int:
        """Get count of cached items.

        Returns:
            Count of items
        """
        ...


@runtime_checkable
class EvictionPolicyProtocol(Protocol):
    """Protocol for cache eviction policy."""

    def get_items_to_evict(self, metadata: Dict[str, Dict[str, Any]], required_space: int, max_size: int) -> List[str]:
        """Get items to evict based on policy.

        Args:
            metadata: Cache metadata
            required_space: Space required for new data in bytes
            max_size: Maximum cache size in bytes

        Returns:
            List of keys to evict
        """
        ...


@runtime_checkable
class CacheManagerProtocol(Protocol):
    """Protocol for cache manager operations."""

    async def get(self, key: str) -> Optional[bytes]:
        """Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found
        """
        ...

    async def set(self, key: str, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Set item in cache.

        Args:
            key: Cache key
            data: Data to cache
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        ...

    async def delete(self, key: str) -> bool:
        """Delete item from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        ...

    async def clear(self) -> bool:
        """Clear all items from cache.

        Returns:
            True if successful, False otherwise
        """
        ...

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        ...
