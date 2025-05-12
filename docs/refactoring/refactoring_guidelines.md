# Refactoring Guidelines for Peri Project

## Introduction

This document provides specific guidance on when and how to refactor code in the Peri project. It complements our existing [coding guidelines](../coding_guidelines.md) and focuses on practical approaches to maintaining code quality through systematic refactoring.

Refactoring is the process of restructuring existing code without changing its external behavior. The goal is to improve non-functional attributes of the software such as readability, complexity, maintainability, and testability.

## When to Refactor

### Code Size Thresholds

Refactoring should be considered when code exceeds these size thresholds:

| Component | Threshold | Action |
|-----------|-----------|--------|
| Class | > 200 lines | Split into multiple classes with clear, focused responsibilities |
| Function/Method | > 50 lines | Break down into smaller functions with single responsibilities |
| File | > 500 lines | Consider splitting into multiple files organized by domain or functionality |
| Nesting | > 3 levels | Simplify by extracting nested code into separate functions |

### Complexity Indicators

Beyond raw size, the following complexity indicators suggest code that needs refactoring:

1. **Cyclomatic Complexity** > 10 for a function or method
2. **Cognitive Complexity** > 15 for a function or method
3. **Maintenance Index** < 65 (as reported by tools like `radon`)
4. **Parameter Count** > 5 for a function or method
5. **Branch Depth** > 3 levels of conditional nesting

### Code Smells

The following "smells" indicate code that likely needs refactoring:

1. **Duplicate Code**: The same code structure appears in more than one place
2. **Long Method**: A method that has grown too large
3. **Large Class**: A class that has taken on too many responsibilities
4. **Too Many Parameters**: A long list of parameters for a method
5. **Divergent Change**: When one class is changed for different reasons
6. **Shotgun Surgery**: When a single change requires changes in multiple classes
7. **Feature Envy**: A method that seems more interested in a class other than the one it belongs to
8. **Data Clumps**: The same group of variables appearing together
9. **Primitive Obsession**: Using primitives instead of small objects for simple tasks
10. **Switch Statements**: Complex conditional logic that could be replaced with polymorphism
11. **Temporary Field**: An instance variable that is only set in certain circumstances
12. **Refused Bequest**: A subclass doesn't use inherited methods or properties
13. **Comments**: Excessive comments often indicate unclear code
14. **Speculative Generality**: Unused abstract classes or unnecessary hooks for anticipated features

## Refactoring Approaches

### For Large Classes

1. **Extract Class**: Identify related attributes and methods that can form a new class
2. **Extract Interface**: Define clear interfaces for different aspects of functionality
3. **Move Method/Field**: Move methods or fields to the class where they're most used
4. **Replace Inheritance with Delegation**: Use composition instead of inheritance where appropriate

#### Example: Splitting a Large Provider Class

```python
# BEFORE: A single large provider class

class KokoroTTSProvider:
    """Kokoro TTS implementation."""
    
    def __init__(self, model_path, voices_dir, cache_dir):
        # Initialization code...
        
    # Voice management methods...
    # Audio generation methods...
    # Model handling methods...
    # Cache interaction methods...
    # ... 200+ lines of code
```

```python
# AFTER: Split into focused classes

class KokoroVoiceManager:
    """Manages voices for Kokoro TTS."""
    
    def __init__(self, voices_dir, default_language):
        # Voice-specific initialization...
        
    async def get_voice(self, voice_id):
        # Voice retrieval logic...
        
    async def get_voices(self):
        # Get all voices...

class KokoroAudioGenerator:
    """Generates audio with Kokoro TTS."""
    
    def __init__(self, model, sample_rate):
        self._model = model
        self._sample_rate = sample_rate
        
    async def generate_speech(self, text, voice, options):
        # Audio generation logic...

class KokoroTTSProvider:
    """Coordinates Kokoro TTS operations."""
    
    def __init__(self, model_path, voices_dir, cache_dir):
        # Create collaborator instances
        self._model_handler = KokoroModelHandler(model_path)
        self._voice_manager = KokoroVoiceManager(voices_dir)
        self._audio_generator = KokoroAudioGenerator(self._model_handler.model)
        
    # Higher-level coordination methods...
```

### For Long Methods

1. **Extract Method**: Break down the method into smaller, focused methods
2. **Replace Temp with Query**: Replace temporary variables with query methods
3. **Introduce Parameter Object**: Replace multiple parameters with an object
4. **Preserve Whole Object**: Pass a whole object instead of multiple fields
5. **Remove Flag Arguments**: Avoid boolean flags, create separate methods instead

#### Example: Breaking Down a Complex Method

```python
# BEFORE: A long, complex method

async def generate_speech(self, text, voice_id, options=None):
    """Generate speech from text."""
    try:
        # Get voice - 10 lines
        # ...
        
        # Process options - 15 lines
        # ...
        
        # Initialize model if needed - 10 lines
        # ...
        
        # Generate audio data - 20 lines
        # ...
        
        # Process audio format - 15 lines
        # ...
        
        # Return result - 5 lines
        # ...
    except Exception as e:
        # Error handling - 10 lines
        # ...
```

```python
# AFTER: Smaller, focused methods

async def generate_speech(self, text, voice_id, options=None):
    """Generate speech from text."""
    try:
        voice = await self._get_voice(voice_id)
        processed_options = self._process_options(options, voice)
        await self._ensure_model_initialized()
        audio_data = await self._generate_audio(text, voice_id, processed_options)
        result = self._format_audio_result(audio_data, voice_id, processed_options)
        return result
    except VoiceNotFoundError:
        raise
    except Exception as e:
        await self._handle_generation_error(e)
        
async def _get_voice(self, voice_id):
    """Get voice by ID."""
    # Voice retrieval logic - 10 lines
    
def _process_options(self, options, voice):
    """Process and validate options."""
    # Options processing - 15 lines
    
# Additional extracted methods...
```

### For Complex Conditionals

1. **Decompose Conditional**: Extract complex conditional expressions into methods
2. **Replace Conditional with Polymorphism**: Use polymorphic objects instead of conditionals
3. **Introduce Null Object**: Use a special case object instead of null checks
4. **Replace Nested Conditional with Guard Clauses**: Use early returns instead of nested conditionals

#### Example: Simplifying Complex Conditionals

```python
# BEFORE: Complex nested conditionals

def process_request(self, request):
    if request.is_authorized():
        if request.has_parameter('format'):
            format = request.get_parameter('format')
            if format in SUPPORTED_FORMATS:
                if request.has_parameter('voice'):
                    voice = request.get_parameter('voice')
                    if voice in available_voices:
                        # Actually process the request
                        return self._process_valid_request(request)
                    else:
                        return Error('Voice not available')
                else:
                    return Error('Voice parameter missing')
            else:
                return Error('Unsupported format')
        else:
            return Error('Format parameter missing')
    else:
        return Error('Not authorized')
```

```python
# AFTER: Using guard clauses

def process_request(self, request):
    # Guard clauses for validation
    if not request.is_authorized():
        return Error('Not authorized')
        
    if not request.has_parameter('format'):
        return Error('Format parameter missing')
        
    format = request.get_parameter('format')
    if format not in SUPPORTED_FORMATS:
        return Error('Unsupported format')
        
    if not request.has_parameter('voice'):
        return Error('Voice parameter missing')
        
    voice = request.get_parameter('voice')
    if voice not in available_voices:
        return Error('Voice not available')
        
    # Main logic when all conditions are met
    return self._process_valid_request(request)
```

## Refactoring for Testability

### Key Principles

1. **Dependency Injection**: Pass dependencies instead of creating them internally
2. **Single Responsibility**: Each class and method should have a clear, single purpose
3. **Interface Segregation**: Use small, specific interfaces instead of large ones
4. **Pure Functions**: Separate computation from I/O or state changes
5. **Testable Units**: Each unit of code should be independently testable

### Example: Refactoring for Testability

```python
# BEFORE: Hard to test due to direct dependencies

class TTSService:
    def __init__(self):
        # Directly creating dependencies
        self.provider = KokoroTTSProvider("path/to/model", "path/to/voices")
        self.cache = CacheManager("/cache/dir")
        
    async def generate_speech(self, text, voice_id):
        # Using internal dependencies directly
        cached_result = self.cache.get(f"{voice_id}:{text}")
        if cached_result:
            return cached_result
            
        result = await self.provider.generate_speech(text, voice_id)
        self.cache.set(f"{voice_id}:{text}", result)
        return result
```

```python
# AFTER: Testable with dependency injection and interfaces

class TTSService:
    def __init__(self, provider: TTSProvider, cache_manager: CacheManager):
        # Dependencies injected
        self._provider = provider
        self._cache = cache_manager
        
    async def generate_speech(self, text, voice_id):
        # Using abstracted interfaces
        cache_key = self._generate_cache_key(text, voice_id)
        
        cached_result = await self._cache.get(cache_key)
        if cached_result:
            return self._create_result_from_cache(cached_result)
            
        result = await self._provider.generate_speech(text, voice_id)
        await self._cache.set(cache_key, result.audio_data, self._get_metadata(result))
        return result
        
    def _generate_cache_key(self, text, voice_id):
        # Extracted method for testing
        return f"tts:{hashlib.md5(f'{voice_id}:{text}'.encode()).hexdigest()}"
```

## Refactoring Process

### Preparation

1. **Ensure Good Test Coverage**: Before refactoring, ensure tests cover the code being changed
2. **Understand the Code**: Make sure you fully understand what the code does before changing it
3. **Create a Backup**: Ensure you can revert if needed
4. **Plan Your Changes**: Document what you intend to change and why

### Step-by-Step Process

1. **Small Steps**: Make small, incremental changes rather than large rewrites
2. **Test After Each Step**: Run tests after each change to ensure behavior remains the same
3. **Commit Frequently**: Create small, focused commits for each refactoring step
4. **Document Rationale**: Note why you made specific refactoring decisions

### Refactoring Workflow

1. **Identify**: Find code that needs refactoring based on the criteria above
2. **Verify**: Ensure sufficient test coverage for the code to be changed
3. **Plan**: Decide which refactoring techniques to apply
4. **Execute**: Make small, incremental changes with frequent testing
5. **Review**: Self-review the changes for quality and behavioral preservation
6. **Commit**: Create a clean, focused commit describing the refactoring
7. **Validate**: Ensure all tests pass after the refactoring is complete

## Tools and Automation

### Recommended Tools

1. **Static Analysis**:
   - `flake8` for general linting
   - `pylint` for more in-depth analysis
   - `mypy` for type checking
   - `radon` for complexity metrics

2. **Refactoring Automation**:
   - IDE refactoring tools (PyCharm, VS Code)
   - `rope` library for Python refactoring

3. **Test Coverage**:
   - `pytest` with `pytest-cov` for coverage reporting

### Example Configuration

```ini
# Setup in pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = --cov=src --cov-report=term --cov-report=html

# Setup in .pylintrc
[MASTER]
disable=
    C0111,  # missing docstring
    C0103,  # invalid name
    C0330,  # bad continuation
    C1801,  # len-as-condition

# Setup in .flake8
[flake8]
max-line-length = 100
max-complexity = 10
```

## Refactoring Documentation

### Documenting Refactoring Decisions

When performing substantial refactoring, document your decisions:

```python
# Before refactoring (in comments or commit message):
#
# Refactoring Rationale:
# - KokoroTTSProvider class had grown to over 300 lines
# - Voice management, audio generation, and model handling were mixed together
# - Testing was difficult due to tight coupling
#
# Refactoring Approach:
# 1. Extract voice management into KokoroVoiceManager
# 2. Extract audio generation into KokoroAudioGenerator
# 3. Extract model handling into KokoroModelHandler
# 4. Keep KokoroTTSProvider as a coordinator class
#
# Expected Benefits:
# - Improved testability through smaller, focused classes
# - Clearer responsibilities and better maintainability
# - Potential for reuse of components in other contexts
```

### Before and After Metrics

Include metrics in your documentation or commit message:

```
Refactoring Metrics:
- Lines of code:                  305 → 320 (slight increase due to interface definitions)
- Average method length:          35 → 12
- Maximum cyclomatic complexity:  15 → 7
- Number of classes:              1 → 4
- Test coverage:                  68% → 85%
```

## Examples

### Real-World Examples in Our Codebase

#### Example 1: Splitting KokoroTTSProvider

The `KokoroTTSProvider` class in `src/tts_service/providers/kokoro_provider.py` has grown to nearly 350 lines and handles multiple responsibilities including:

1. Voice management
2. Audio generation
3. Model initialization and management
4. Language handling

This class should be refactored by:

1. Extracting a `KokoroVoiceManager` class
2. Extracting a `KokoroAudioGenerator` class
3. Extracting a `KokoroModelHandler` class
4. Keeping `KokoroTTSProvider` as a coordinator class

#### Example 2: Breaking Down generate_speech Method

The `generate_speech` method in `src/tts_service/services/tts_service.py` is over 50 lines and has multiple responsibilities:

1. Cache checking
2. Provider selection
3. Speech generation
4. Cache updating

This method should be refactored by:

1. Extracting `_check_cache` and `_update_cache` methods
2. Extracting `_select_provider` method
3. Simplifying the main method to coordinate these operations

## Conclusion

Effective refactoring is crucial for maintaining code quality as the Peri project evolves. By following these guidelines, we can ensure that our codebase remains maintainable, testable, and adaptable to changing requirements.

Remember that refactoring is not a one-time activity but an ongoing practice that should be integrated into your regular development workflow. Small, incremental improvements are often more effective than large rewrites.

When in doubt, prioritize readability, simplicity, and testability over cleverness or optimization.
