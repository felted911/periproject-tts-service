# Exceptions for the TTS service
from typing import Dict, Any, Optional


class TTSError(Exception):
    """Base exception for all TTS service errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


# Validation errors
class ValidationError(TTSError):
    """Raised when input validation fails."""

    pass


class InvalidTextError(ValidationError):
    """Raised when the input text is invalid."""

    pass


class InvalidOptionsError(ValidationError):
    """Raised when TTS options are invalid."""

    pass


# Resource errors
class ResourceError(TTSError):
    """Raised when a required resource is unavailable."""

    pass


class ModelNotFoundError(ResourceError):
    """Raised when a TTS model cannot be found."""

    pass


class VoiceNotFoundError(ResourceError):
    """Raised when a voice cannot be found."""

    pass


# Service errors
class ServiceError(TTSError):
    """Raised when a service dependency fails."""

    pass


class ModelLoadError(ServiceError):
    """Raised when loading a model fails."""

    pass


class GenerationFailedError(ServiceError):
    """Raised when speech generation fails."""

    pass


# Internal errors
class InternalError(TTSError):
    """Raised when an unexpected internal error occurs."""

    pass


# Configuration errors
class ConfigurationError(TTSError):
    """Raised when there is an issue with configuration."""

    pass


# Provider errors
class ProviderError(TTSError):
    """Raised when a TTS provider operation fails."""

    pass


class ProviderNotAvailableError(ProviderError):
    """Raised when a TTS provider is not available."""

    pass


# Cache errors
class CacheError(TTSError):
    """Raised when a cache operation fails."""

    pass


class CacheIOError(CacheError):
    """Raised when I/O operations fail during cache operations."""

    pass


class CachePermissionError(CacheError):
    """Raised when permission errors occur during cache operations."""

    pass


class CacheDiskFullError(CacheError):
    """Raised when there's insufficient disk space for cache operations."""

    pass


class CacheMetadataError(CacheError):
    """Raised when handling cache metadata fails."""

    pass


class CacheSerializationError(CacheError):
    """Raised when serialization or deserialization of cache data fails."""

    pass


class CacheConcurrencyError(CacheError):
    """Raised when concurrent access issues occur during cache operations."""

    pass
