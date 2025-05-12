# Refactoring Task List

This document outlines the current refactoring tasks identified in the Peri project, prioritized by importance and expected impact.

## High Priority Tasks

### Task #1: Split Large Class - KokoroTTSProvider
- **File**: `src/tts_service/providers/kokoro_provider.py`
- **Lines**: 50-399
- **Guideline Violation**: "Large Classes" - Split classes with more than 200 lines of code
- **Action**: Refactor the KokoroTTSProvider class into smaller, more focused classes
- **Implementation Notes**: Split into separate classes for voice management, audio generation, and model handling. Current class is nearly 350 lines of code, well over the 200-line guideline.

### Task #2: Split Large Class - CacheManager
- **File**: `src/tts_service/infrastructure/cache.py`
- **Lines**: 13-270
- **Guideline Violation**: "Large Classes" - Split classes with more than 200 lines of code
- **Action**: Refactor the CacheManager class into smaller, more focused classes
- **Implementation Notes**: Extract the file handling logic and metadata management into separate classes. Current class is approximately 260 lines of code, exceeding the 200-line guideline.

### Task #3: Fix Incomplete Error Handling in TTS Service
- **File**: `src/tts_service/services/tts_service.py`
- **Lines**: 91-108
- **Guideline Violation**: "Incomplete Error Handling" - AI often misses error cases
- **Action**: Add proper error handling for when no providers are available when calling `get_provider_info()`
- **Implementation Notes**: The `get_provider_info()` method catches exceptions for individual providers but doesn't handle the case where no providers are available at all. Add a check and appropriate error handling.

### Task #4: Fix Missing Edge Case in Error Handling for TTS Router
- **File**: `src/tts_service/api/routers/tts.py`
- **Lines**: 51-61
- **Guideline Violation**: "Missing Edge Cases" - Review AI-generated code for edge cases
- **Action**: Add error handling for cases where text is too long (exceeds MAX_TEXT_LENGTH from settings)
- **Implementation Notes**: Validate the text length before generating speech, raising a ValidationError if it exceeds the limit.

### Task #5: Improve Error Handling in Cache Manager
- **File**: `src/tts_service/infrastructure/cache.py`
- **Lines**: 108-136
- **Guideline Violation**: "Realistic Error Handling" - Error cases should have specific, not generic, handling
- **Action**: Improve error handling in the set method to handle specific error types
- **Implementation Notes**: Add specific error handling for different types of exceptions that might occur during file operations.

### Task #6: Add Missing Edge Case in TTS Service for Multiple Provider Support
- **File**: `src/tts_service/services/tts_service.py`
- **Lines**: 162-194
- **Guideline Violation**: "Missing Edge Cases" - Review AI-generated code for edge cases
- **Action**: Add error handling for the case where a provider is specified but doesn't have the requested voice
- **Implementation Notes**: Currently, if a provider is specified but doesn't have the requested voice, a VoiceNotFoundError is raised, but there's no attempt to try other providers. Consider adding fallback logic.

## Medium Priority Tasks

### Task #7: Split Complex Function - generate_speech in KokoroTTSProvider
- **File**: `src/tts_service/providers/kokoro_provider.py`
- **Lines**: 167-233
- **Guideline Violation**: "Complex Functions" - Refactor functions longer than 50 lines
- **Action**: Split the generate_speech method into smaller, more focused functions
- **Implementation Notes**: Extract the language code conversion, audio generation, and format conversion into separate helper methods to reduce complexity and enhance readability.

### Task #8: Split Complex Function - generate_speech in TTSService
- **File**: `src/tts_service/services/tts_service.py`
- **Lines**: 110-168
- **Guideline Violation**: "Complex Functions" - Refactor functions longer than 50 lines
- **Action**: Split the generate_speech method into smaller, more focused functions
- **Implementation Notes**: Extract the provider selection logic and caching logic into separate methods to reduce complexity.

### Task #9: Add Interface Abstraction for Cache Manager
- **File**: `src/tts_service/infrastructure/cache.py`
- **Lines**: 13-270
- **Guideline Violation**: "Interface Abstraction" - Create interfaces for external services
- **Action**: Create a Protocol class for the CacheManager to define its interface
- **Implementation Notes**: Create a CacheManagerProtocol class in the same file, following the same pattern as in tts_provider.py.

### Task #10: Add Missing Interface for TTSService
- **File**: `src/tts_service/services/tts_service.py`
- **Lines**: 16-266
- **Guideline Violation**: "Interface Segregation" - Create small, specific interfaces
- **Action**: Create a Protocol class that defines the TTSService interface
- **Implementation Notes**: Create a TTSServiceProtocol class similar to the TTSProvider protocol, defining the interface for the service.

### Task #11: Remove Hardcoded Values in Kokoro Provider
- **File**: `src/tts_service/providers/kokoro_provider.py`
- **Lines**: 94-96
- **Guideline Violation**: "No Hard-coded Values" - All magic numbers and strings should be properly defined as constants
- **Action**: Replace hardcoded sample rate (24000) with a constant or configuration value
- **Implementation Notes**: Use the sample rate from settings (`settings.KOKORO_SETTINGS["sampling_rate"]`) instead of hardcoding 24000.

### Task #12: Extract Pure Functions in Kokoro Provider
- **File**: `src/tts_service/providers/kokoro_provider.py`
- **Lines**: 345-399
- **Guideline Violation**: "Pure Functions" - Extract pure computational logic from I/O operations
- **Action**: Extract the `_load_voice_metadata` method's hardcoded data into a separate function or config file
- **Implementation Notes**: This is a testing/development implementation, but should still follow the guideline by moving the hardcoded voice metadata to a more appropriate location.

### Task #13: Remove Debugging Code from KokoroTTSProvider
- **File**: `src/tts_service/providers/kokoro_provider.py`
- **Lines**: 18-45
- **Guideline Violation**: "No Debug Code" - All debugging print statements and commented-out code should be removed
- **Action**: Replace the mock implementation with a proper error handling mechanism
- **Implementation Notes**: Instead of the mock implementation, consider using the Protocol pattern to define the interface and raising a clear error when the Kokoro module isn't available.

### Task #14: Fix Duplicate Code in Voice Handling
- **File**: `src/tts_service/providers/kokoro_provider.py`
- **Lines**: 198-220, 280-314
- **Guideline Violation**: "Duplicate Code" - If you find the same code pattern repeated 3+ times, refactor to remove duplication
- **Action**: Extract the voice validation logic into a separate method to avoid duplication
- **Implementation Notes**: Create a _validate_voice method that can be reused across different methods to check voice validity.

## Low Priority Tasks

### Task #15: Add Missing Type Hints in Download Models Utility
- **File**: `src/utils/download_models.py`
- **Lines**: 14-68
- **Guideline Violation**: "Type Hints" - All function parameters and return values should have type hints
- **Action**: Add return type hints for all functions
- **Implementation Notes**: Add -> None return type annotations to the download_file and download_kokoro_models functions.

### Task #16: Add Missing Docstring in Main Application
- **File**: `src/main.py`
- **Lines**: 45-52
- **Guideline Violation**: "Docstrings" - All public functions, classes, and methods must have docstrings
- **Action**: Add docstring to the error handler
- **Implementation Notes**: Add appropriate Google-style docstrings to the error handler functions.

### Task #17: Fix Large Function in Download Models Utility
- **File**: `src/utils/download_models.py`
- **Lines**: 14-35
- **Guideline Violation**: "Complex Functions" - Refactor functions longer than 50 lines or with more than 3 levels of nesting
- **Action**: Split the download_file function into smaller, more focused functions
- **Implementation Notes**: Extract the progress bar handling into a separate function to reduce complexity.

### Task #18: Improve Documentation in TTS Service Constructor
- **File**: `src/tts_service/services/tts_service.py`
- **Lines**: 22-35
- **Guideline Violation**: "Docstrings" - All public functions, classes, and methods must have docstrings
- **Action**: Improve the docstring for the TTSService constructor to better explain its parameters
- **Implementation Notes**: Add more detailed descriptions of what each parameter is for and any constraints they might have.

## Tracking Progress

This task list is maintained and updated as refactoring work progresses. When completing a task:

1. Move it to the "Completed Tasks" section below
2. Add the date of completion and the PR number
3. Include brief notes on the approach taken

### Task #19: Fix Unawaited Coroutine in Cache Manager
- **File**: `src/tts_service/infrastructure/cache/cache_manager.py`
- **Lines**: 420-440 (the _load_metadata method)
- **Guideline Violation**: "Proper Async/Sync Boundaries" - Async functions should be properly awaited
- **Action**: Refactor the metadata loading to properly handle async operations
- **Priority**: Medium
- **Implementation Notes**: The current implementation tries to run an async function synchronously which causes warnings. Consider making the entire class async or implement a proper sync version of metadata loading. Currently triggers a RuntimeWarning: `coroutine 'MetadataManager.load' was never awaited` in test execution.

## Completed Tasks

*No tasks completed yet*
