"""Metadata manager for cache operations."""

import json
import time
import asyncio
from pathlib import Path
import aiofiles
from typing import Dict, Any, Optional, List

from ..logging import get_logger
from ..exceptions import (
    CacheMetadataError, CachePermissionError, CacheIOError, 
    CacheSerializationError, CacheDiskFullError, CacheConcurrencyError
)
from .protocols import CacheMetadataProtocol

logger = get_logger(__name__)


class MetadataManager:
    """Manager for cache metadata operations."""
    
    def __init__(self, metadata_file: Path, ttl: int):
        """Initialize metadata manager.
        
        Args:
            metadata_file: File to store metadata
            ttl: Time-to-live for cached items in seconds
        """
        self.metadata_file = metadata_file
        self.ttl = ttl
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()  # Add a lock for thread safety
        
    async def load(self) -> None:
        """Load metadata from storage.
        
        Raises:
            CacheIOError: If there's an I/O error reading the metadata file
            CacheSerializationError: If the metadata file contains invalid JSON
            CachePermissionError: If there's a permission error accessing the metadata file
        """
        async with self._lock:
            try:
                # Check if metadata file exists
                if not self.metadata_file.exists():
                    logger.debug("Metadata file not found, creating empty metadata")
                    self.metadata = {}
                    return
                    
                # Read metadata
                try:
                    async with aiofiles.open(self.metadata_file, "r") as f:
                        metadata_str = await f.read()
                except PermissionError as e:
                    logger.error(f"Metadata load permission error: {str(e)}")
                    raise CachePermissionError(f"Permission denied when loading metadata: {str(e)}", 
                                             {"file_path": str(self.metadata_file)}) from e
                except OSError as e:
                    logger.error(f"Metadata load I/O error: {str(e)}")
                    raise CacheIOError(f"I/O error during metadata load: {str(e)}",
                                     {"file_path": str(self.metadata_file)}) from e
                
                # Parse JSON
                try:
                    self.metadata = json.loads(metadata_str) if metadata_str.strip() else {}
                except json.JSONDecodeError as e:
                    logger.error(f"Metadata parse error: {str(e)}")
                    raise CacheSerializationError(f"Failed to parse metadata JSON: {str(e)}", 
                                               {"file_path": str(self.metadata_file)}) from e
                    
                # Clean up expired items
                self._clean_expired_items()
                    
                logger.debug(f"Loaded cache metadata: {len(self.metadata)} items")
                    
            except (CachePermissionError, CacheIOError, CacheSerializationError):
                # Re-raise specific exceptions
                raise
            except Exception as e:
                logger.exception(f"Unexpected error loading cache metadata: {str(e)}")
                # Reset metadata to empty dict on error
                self.metadata = {}
                raise CacheMetadataError(f"Unexpected error loading cache metadata: {str(e)}") from e
            
    async def save(self) -> None:
        """Save metadata to storage.
        
        Raises:
            CachePermissionError: When permission issues occur
            CacheIOError: When file I/O operations fail
            CacheSerializationError: When JSON serialization fails
            CacheDiskFullError: When disk space is insufficient
            CacheConcurrencyError: When metadata has been modified by another process
        """
        async with self._lock:
            try:
                # Write metadata to temporary file
                temp_file = self.metadata_file.with_suffix(".tmp")
                
                # Serialize metadata
                try:
                    metadata_json = json.dumps(self.metadata, indent=2)
                except (TypeError, ValueError, OverflowError) as e:
                    logger.error(f"Failed to serialize cache metadata: {str(e)}")
                    raise CacheSerializationError(f"Failed to serialize cache metadata: {str(e)}", 
                                                {"metadata_size": len(self.metadata)}) from e
                    
                # Write metadata to temporary file
                try:
                    async with aiofiles.open(temp_file, "w") as f:
                        await f.write(metadata_json)
                except PermissionError as e:
                    logger.error(f"Cache metadata permission error: {str(e)}")
                    raise CachePermissionError(f"Permission denied when saving metadata: {str(e)}", 
                                            {"file_path": str(temp_file)}) from e
                except OSError as e:
                    # OSError with errno 28 is "No space left on device"
                    if hasattr(e, 'errno') and e.errno == 28:
                        logger.error(f"Cache metadata disk full error: {str(e)}")
                        raise CacheDiskFullError(f"Insufficient disk space for metadata: {str(e)}",
                                                {"file_path": str(temp_file)}) from e
                    else:
                        logger.error(f"Cache metadata I/O error: {str(e)}")
                        raise CacheIOError(f"I/O error during metadata save: {str(e)}",
                                        {"file_path": str(temp_file)}) from e
                    
                # Rename temporary file to metadata file
                try:
                    if self.metadata_file.exists():
                        # On Windows, we need to remove the existing file first
                        self.metadata_file.unlink()
                    temp_file.rename(self.metadata_file)
                except OSError as e:
                    logger.error(f"Failed to rename metadata file: {str(e)}")
                    raise CacheIOError(f"Failed to rename metadata file: {str(e)}",
                                    {"temp_file": str(temp_file), 
                                     "metadata_file": str(self.metadata_file)}) from e
                    
                logger.debug(f"Saved cache metadata: {len(self.metadata)} items")
                    
            except (CachePermissionError, CacheIOError, CacheSerializationError, CacheDiskFullError, CacheConcurrencyError):
                # Re-raise specific exceptions
                raise
            except Exception as e:
                logger.exception(f"Unexpected error saving cache metadata: {str(e)}")
                raise CacheMetadataError(f"Unexpected error saving cache metadata: {str(e)}") from e
            
    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for cache item.
        
        Args:
            key: Cache key
            
        Returns:
            Metadata or None if not found
        """
        return self.metadata.get(key)
        
    def set_metadata(self, key: str, file_name: str, size: int, custom_metadata: Optional[Dict[str, Any]] = None) -> None:
        """Set metadata for cache item.
        
        Args:
            key: Cache key
            file_name: Name of cache file
            size: Size of cached data in bytes
            custom_metadata: Additional metadata
        """
        now = time.time()
        self.metadata[key] = {
            "file_name": file_name,
            "size": size,
            "created_at": now,
            "last_accessed": now,
            "expires_at": now + self.ttl,
            "meta": custom_metadata or {},
        }
        
    def delete_metadata(self, key: str) -> bool:
        """Delete metadata for cache item.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if key not in self.metadata:
            return False
            
        del self.metadata[key]
        return True
        
    def clear_metadata(self) -> None:
        """Clear all metadata."""
        self.metadata = {}
        
    def update_access_time(self, key: str) -> None:
        """Update last accessed time for cache item.
        
        Args:
            key: Cache key
        """
        if key in self.metadata:
            self.metadata[key]["last_accessed"] = time.time()
            
    def is_expired(self, key: str) -> bool:
        """Check if cache item is expired.
        
        Args:
            key: Cache key
            
        Returns:
            True if expired, False otherwise
        """
        if key not in self.metadata:
            return True
            
        return time.time() > self.metadata[key]["expires_at"]
        
    def _clean_expired_items(self) -> List[str]:
        """Remove expired items from metadata.
        
        Returns:
            List of expired keys that were removed
        """
        now = time.time()
        expired_keys = [
            key for key, item in self.metadata.items()
            if now > item.get("expires_at", 0)
        ]
        
        for key in expired_keys:
            del self.metadata[key]
            
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache items")
            
        return expired_keys
        
    def get_all_keys(self) -> List[str]:
        """Get all cache keys.
        
        Returns:
            List of cache keys
        """
        return list(self.metadata.keys())
        
    def get_metadata_size(self) -> int:
        """Get total size of cached items in bytes.
        
        Returns:
            Total size in bytes
        """
        return sum(item["size"] for item in self.metadata.values())
        
    def get_metadata_count(self) -> int:
        """Get count of cached items.
        
        Returns:
            Count of items
        """
        return len(self.metadata)
