"""Cache manager for the TTS service."""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..logging import get_logger
from ..exceptions import (
    CacheError, CacheIOError, CachePermissionError, 
    CacheDiskFullError, CacheMetadataError, CacheSerializationError
)
from config import settings
from .protocols import CacheManagerProtocol, CacheStorageProtocol, CacheMetadataProtocol, EvictionPolicyProtocol
from .file_storage import FileStorage
from .metadata_manager import MetadataManager
from .eviction_policy import LRUEvictionPolicy

logger = get_logger(__name__)


class CacheManager(CacheManagerProtocol):
    """Manager for caching generated audio.
    
    This class orchestrates the caching operations, delegating specific
    responsibilities to specialized components:
    - FileStorage: Handles file I/O operations
    - MetadataManager: Manages cache metadata
    - EvictionPolicy: Determines which items to evict when cache is full
    """
    
    def __init__(
        self,
        cache_dir: str = settings.CACHE_DIR,
        enabled: bool = settings.CACHE_ENABLED,
        ttl: int = settings.CACHE_TTL,
        max_size: int = settings.MAX_CACHE_SIZE,
        storage: Optional[CacheStorageProtocol] = None,
        metadata_manager: Optional[CacheMetadataProtocol] = None,
        eviction_policy: Optional[EvictionPolicyProtocol] = None,
    ):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cached files
            enabled: Whether caching is enabled
            ttl: Time-to-live for cached items in seconds
            max_size: Maximum cache size in bytes
            storage: Custom storage implementation
            metadata_manager: Custom metadata manager implementation
            eviction_policy: Custom eviction policy implementation
        """
        self.cache_dir = Path(cache_dir)  # Kept for backward compatibility
        self.enabled = enabled
        self.ttl = ttl
        self.max_size = max_size
        
        # Create or use provided components
        self._storage = storage or FileStorage(cache_dir)
        
        metadata_file = self.cache_dir / "metadata.json"
        self._metadata = metadata_manager or MetadataManager(metadata_file, ttl)
        
        self._eviction_policy = eviction_policy or LRUEvictionPolicy()
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Load metadata
        self._load_metadata()
        
        logger.debug(
            f"Cache manager initialized",
            extra={
                "cache_dir": str(self.cache_dir),
                "enabled": self.enabled,
                "ttl": self.ttl,
                "max_size": self.max_size,
            },
        )
    
    async def get(self, key: str) -> Optional[bytes]:
        """Get item from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached data or None if not found or error occurs
        """
        if not self.enabled:
            return None
        
        try:
            # Check if key exists in metadata
            metadata_item = self._metadata.get_metadata(key)
            if not metadata_item:
                logger.debug(f"Cache miss: {key}")
                return None
            
            # Check if item is expired
            if self._metadata.is_expired(key):
                logger.debug(f"Cache expired: {key}")
                await self.delete(key)
                return None
            
            # Read data from storage
            try:
                data = await self._storage.read(key)
                if data is None:
                    logger.warning(f"Cache metadata exists but file missing: {key}")
                    await self.delete(key)
                    return None
            except CacheIOError as e:
                logger.error(f"I/O error reading cache: {str(e)}")
                return None
            except CachePermissionError as e:
                logger.error(f"Permission error reading cache: {str(e)}")
                return None
            
            # Update last accessed time
            self._metadata.update_access_time(key)
            try:
                await self._metadata.save()
            except (CacheIOError, CachePermissionError, CacheSerializationError, CacheDiskFullError) as e:
                # Log but continue - non-critical error for reads
                logger.warning(f"Failed to update access time in metadata: {str(e)}")
            
            logger.debug(f"Cache hit: {key}", extra={"size": len(data)})
            return data
            
        except Exception as e:
            logger.exception(f"Cache get error: {str(e)}")
            # Don't propagate cache errors to callers
            return None
    
    async def set(self, key: str, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Set item in cache.
        
        Args:
            key: Cache key
            data: Data to cache
            metadata: Additional metadata
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Check cache size before adding and evict if needed
            await self._ensure_cache_size(len(data))
            
            # Get file name and path
            file_path = await self._storage.get_file_path(key)
            file_name = file_path.name
            
            # Handle storage write operation with comprehensive error handling
            try:
                # Write data to storage
                await self._storage.write(key, data)
            except CachePermissionError as e:
                # Handle permission errors
                logger.error(f"Permission error during cache write: {str(e)}")
                return False
            except CacheDiskFullError as e:
                # Handle disk full errors with recovery attempt
                logger.error(f"Disk full error during cache write: {str(e)}")
                try:
                    # Try to free up space by forcing cache eviction
                    await self._force_eviction(len(data))
                    # Retry the write operation
                    await self._storage.write(key, data)
                except Exception as retry_error:
                    logger.error(f"Failed to recover from disk full error: {str(retry_error)}")
                    return False
            except CacheIOError as e:
                # Handle general I/O errors
                logger.error(f"I/O error during cache write: {str(e)}")
                return False
            
            # If we've made it here, the data was successfully written
            # Now update metadata
            self._metadata.set_metadata(key, file_name, len(data), metadata)
            
            # Handle metadata save operation with comprehensive error handling
            try:
                await self._metadata.save()
            except CacheSerializationError as e:
                # Handle JSON serialization errors
                logger.error(f"Serialization error during metadata save: {str(e)}")
                # Clean up the data file since metadata couldn't be saved
                try:
                    await self._storage.delete(key)
                except Exception as cleanup_error:
                    logger.error(f"Failed to clean up after metadata save error: {str(cleanup_error)}")
                return False
            except (CachePermissionError, CacheIOError, CacheDiskFullError) as e:
                # Handle file system errors
                logger.error(f"File system error during metadata save: {str(e)}")
                # Clean up the data file since metadata couldn't be saved
                try:
                    await self._storage.delete(key)
                except Exception as cleanup_error:
                    logger.error(f"Failed to clean up after metadata save error: {str(cleanup_error)}")
                return False
            
            logger.debug(f"Cache set: {key}", extra={"size": len(data)})
            return True
            
        except Exception as e:
            logger.exception(f"Unexpected cache set error: {str(e)}")
            # Don't propagate cache errors to callers
            return False
            
    async def _force_eviction(self, required_space: int) -> None:
        """Force eviction of cache items to free up space.
        
        This is a more aggressive version of _ensure_cache_size that tries to free up
        space by evicting a larger portion of the cache.
        
        Args:
            required_space: Size of data needing to be cached in bytes
        """
        if not self.enabled:
            return
            
        try:
            # Simple approach: just delete oldest items until we have enough space
            if not self._metadata.metadata:
                # Nothing to evict
                return
                
            # Sort items by last_accessed (oldest first)
            items = sorted(
                self._metadata.metadata.items(),
                key=lambda item: item[1]["last_accessed"]
            )
            
            # Track how much space we've freed and how many items evicted
            space_freed = 0
            evicted_count = 0
            
            # Evict items one by one until we have freed enough space
            for key, item in items:
                # Don't evict more than we need
                if space_freed >= required_space:
                    break
                    
                # Try to delete the item
                size = item["size"]
                success = await self.delete(key)
                
                # Only count successfully deleted items
                if success:
                    space_freed += size
                    evicted_count += 1
            
            # Log what we did
            if evicted_count > 0:
                logger.info(
                    f"Force-evicted {evicted_count} items to free {space_freed} bytes",
                    extra={"required_space": required_space}
                )
                
        except Exception as e:
            # Log but don't propagate - this should never break the app
            logger.exception(f"Error during force eviction: {str(e)}")
    
    async def delete(self, key: str) -> bool:
        """Delete item from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or key not in self._metadata.get_all_keys():
            return False
        
        try:
            # Delete from storage with specific error handling
            try:
                if not await self._storage.delete(key):
                    return False
            except CachePermissionError as e:
                logger.error(f"Permission error during cache delete: {str(e)}")
                return False
            except CacheIOError as e:
                logger.error(f"I/O error during cache delete: {str(e)}")
                return False
            
            # Delete from metadata
            self._metadata.delete_metadata(key)
            
            # Save metadata with specific error handling
            try:
                await self._metadata.save()
            except (CacheSerializationError, CachePermissionError, CacheIOError, CacheDiskFullError) as e:
                logger.error(f"Error saving metadata after deletion: {str(e)}")
                # The file is already deleted, but metadata couldn't be saved
                # This creates an inconsistent state, but we can't restore the file
                return False
            
            logger.debug(f"Cache delete: {key}")
            return True
            
        except Exception as e:
            logger.exception(f"Cache delete error: {str(e)}")
            # Don't propagate cache errors to callers
            return False
    
    async def clear(self) -> bool:
        """Clear all items from cache.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Clear storage with specific error handling
            try:
                if not await self._storage.clear():
                    return False
            except CachePermissionError as e:
                logger.error(f"Permission error during cache clear: {str(e)}")
                return False
            except CacheIOError as e:
                logger.error(f"I/O error during cache clear: {str(e)}")
                return False
            
            # Clear metadata
            self._metadata.clear_metadata()
            
            # Save metadata with specific error handling
            try:
                await self._metadata.save()
            except (CacheSerializationError, CachePermissionError, CacheIOError, CacheDiskFullError) as e:
                logger.error(f"Error saving metadata after clearing: {str(e)}")
                # Files are already deleted, but we need to restore metadata for consistency
                # Create empty metadata
                return False
            
            logger.info("Cache cleared")
            return True
            
        except Exception as e:
            logger.exception(f"Cache clear error: {str(e)}")
            # Don't propagate cache errors to callers
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        if not self.enabled:
            return {
                "enabled": False,
                "count": 0,
                "size": 0,
                "max_size": self.max_size,
            }
        
        # Calculate stats
        count = self._metadata.get_metadata_count()
        size = self._metadata.get_metadata_size()
        
        return {
            "enabled": True,
            "count": count,
            "size": size,
            "max_size": self.max_size,
            "ttl": self.ttl,
            "usage_percent": (size / self.max_size) * 100 if self.max_size > 0 else 0,
        }
    
    async def _ensure_cache_size(self, new_data_size: int) -> None:
        """Ensure cache size is within limits by evicting items if necessary.
        
        Args:
            new_data_size: Size of new data to add
        """
        if not self.enabled:
            return
        
        try:
            # Calculate current cache size
            current_size = self._metadata.get_metadata_size()
            
            # Check if adding new data would exceed max size
            if current_size + new_data_size <= self.max_size:
                return
            
            logger.info(
                f"Cache size would exceed limit, evicting items",
                extra={
                    "current_size": current_size,
                    "new_data_size": new_data_size,
                    "max_size": self.max_size,
                },
            )
            
            # Get items to evict using the eviction policy
            keys_to_evict = self._eviction_policy.get_items_to_evict(
                self._metadata.metadata,  # Pass full metadata dictionary
                new_data_size,
                self.max_size
            )
            
            # Evict items
            space_freed = 0
            for key in keys_to_evict:
                item_size = self._metadata.get_metadata(key)["size"]
                success = await self.delete(key)
                if success:
                    space_freed += item_size
            
            if keys_to_evict:
                logger.debug(
                    f"Freed enough space for new data",
                    extra={
                        "space_freed": space_freed,
                        "items_evicted": len(keys_to_evict),
                    },
                )
        except Exception as e:
            # Log but continue - we'll let the write operation decide if there's enough space
            logger.error(f"Error ensuring cache size: {str(e)}")
    
    def _load_metadata(self) -> None:
        """Load cache metadata."""
        if not self.enabled:
            return
            
        # Use a more robust approach for handling asyncio in synchronous contexts
        try:
            # Try to get the current event loop in a future-proof way
            try:
                # Python 3.10+
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except AttributeError:
                # Fallback for older Python versions
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
            # Check if loop is running
            if loop.is_running():
                # If the loop is already running, we're in an async context
                # So we create a task to run later and set an empty metadata for now
                self._metadata.metadata = {}
                asyncio.create_task(self._async_load_metadata())
            else:
                # Loop is not running, we can use run_until_complete
                loop.run_until_complete(self._metadata.load())
        except Exception as e:
            logger.exception(f"Unexpected error loading metadata: {str(e)}")
            # Initialize with empty metadata on error
            self._metadata.metadata = {}
            
    async def _async_load_metadata(self) -> None:
        """Asynchronously load metadata when in an async context."""
        try:
            await self._metadata.load()
        except (CacheSerializationError, CachePermissionError, CacheIOError) as e:
            logger.error(f"Failed to load metadata: {str(e)}")
            # Initialize with empty metadata on error
            self._metadata.metadata = {}
        except Exception as e:
            logger.exception(f"Unexpected error loading metadata: {str(e)}")
            # Initialize with empty metadata on error
            self._metadata.metadata = {}
