# Python Coding Guidelines for AI-Assisted Development

This document outlines the coding guidelines for the Peri project's Python components, with a focus on AI-assisted development practices. These guidelines are designed to ensure code quality, maintainability, and testability while leveraging AI tools for development.

## General Principles

### Code Structure

- **Modular Design**: Organize code into small, focused modules with clear responsibilities
- **Single Responsibility**: Each class or function should have a single purpose
- **Dependency Injection**: Use dependency injection to make components testable and loosely coupled
- **Interface Segregation**: Create small, specific interfaces rather than large, general-purpose ones

### Documentation

- **Docstrings**: All public functions, classes, and methods must have docstrings following Google style
- **Type Hints**: Use Python type hints for all function parameters and return values
- **README Files**: Each directory should have a README.md explaining its purpose
- **Examples**: Include code examples in documentation for complex functionality

## AI-Specific Guidelines

### Prompting Best Practices

- **Be Explicit**: Clearly define the purpose and expected behavior of requested code
- **Provide Context**: Include information about the broader system and how the component fits in
- **Request Explanations**: Ask AI to explain complex algorithms or patterns it generates
- **Specify Requirements**: Explicitly state performance, reliability, and error handling requirements

### AI Output Review

- **Never Use AI-Generated Code Without Review**: Always review and understand generated code
- **Check Edge Cases**: Verify that AI-generated code handles edge cases properly
- **Verify Error Handling**: Ensure proper error handling in AI-generated code
- **Test Thoroughly**: Always create tests for AI-generated components

## Refactoring Guidelines

### When to Refactor

- **Duplicate Code**: If you find the same code pattern repeated 3+ times, refactor to remove duplication
- **Complex Functions**: Refactor functions longer than 50 lines or with more than 3 levels of nesting
- **Large Classes**: Split classes with more than 200 lines of code or 10+ methods
- **High Cyclomatic Complexity**: Refactor functions with a cyclomatic complexity > 10

### Refactoring for Testability

- **Extract Dependencies**: Move external dependencies to parameters for better mocking
- **Interface Abstraction**: Create interfaces for external services
- **Pure Functions**: Extract pure computational logic from I/O operations
- **Testable Units**: Ensure each unit of code is independently testable

### Common AI Refactoring Pitfalls

- **Incomplete Error Handling**: AI often misses error cases - ensure all exceptions are handled
- **Undocumented Dependencies**: Explicitly document all dependencies in AI-generated code
- **Missing Edge Cases**: Review AI-generated code for edge cases, especially with user input
- **Overly Clever Solutions**: Prefer readability over cleverness in AI-generated algorithms

## Testing Standards

### Test Coverage

- **Minimum Coverage**: Aim for 80%+ code coverage on all new code
- **Critical Path**: Ensure 100% coverage for critical business logic
- **Edge Cases**: Write tests for boundary conditions and error paths
- **Integration Tests**: Include integration tests for component interactions

### Test Structure

- **Arrange-Act-Assert**: Structure tests with clear setup, action, and verification sections
- **Test Independence**: Each test should be independent and not rely on other tests
- **Mocking**: Use mocks for external dependencies, but prefer integration tests when practical
- **Property-Based Testing**: Use property-based testing for algorithmic code

## Code Quality Tools

### Static Analysis

- **Linting**: Use flake8 and pylint for static analysis
- **Type Checking**: Use mypy for static type checking
- **Security Analysis**: Run bandit for security vulnerability detection
- **Complexity Analysis**: Monitor cyclomatic complexity with radon

### Continuous Integration

- **Automated Testing**: Run all tests on each commit
- **Quality Gates**: Enforce quality standards through CI gates
- **Performance Testing**: Include performance tests for critical paths
- **Documentation Generation**: Automatically generate API documentation

## Examples

### Good Example (Clear, Testable, Well-Structured)

```python
class TTSService:
    """Service for text-to-speech conversion using Kokoro TTS."""

    def __init__(self, model_provider: ModelProvider, cache_manager: CacheManager):
        """Initialize the TTS service.
        
        Args:
            model_provider: Provider for TTS models
            cache_manager: Manager for audio cache
        """
        self._model_provider = model_provider
        self._cache_manager = cache_manager
        self._current_model = None
    
    async def get_voices(self) -> List[Voice]:
        """Get available voices for the current model.
        
        Returns:
            List of available voices
        
        Raises:
            ModelNotLoadedError: If no model is currently loaded
        """
        if not self._current_model:
            raise ModelNotLoadedError("No model is currently loaded")
            
        # Implementation details...
```

### Bad Example (AI Common Mistakes)

```python
# DON'T DO THIS
class TTSManager:
    def __init__(self):
        self.model = KPipeline(lang_code='a')  # Hardcoded dependency
        
    def process_text(self, text, voice="default", speed=1.0, out_file=None):
        # No error handling
        generator = self.model(text, voice=voice)
        for i, (gs, ps, audio) in enumerate(generator):
            if out_file:
                sf.write(out_file, audio, 24000)  # Hardcoded sample rate
            return audio  # Only returns first chunk
```

## Best Practices for Service Development

- **Use Dependency Injection**: Make dependencies explicit through constructor parameters
- **Create Service Interfaces**: Define interfaces to enable swapping implementations
- **Handle Asynchronous Operations**: Use async/await for I/O-bound operations
- **Implement Proper Error Handling**: Define custom exceptions and handle errors appropriately
- **Add Instrumentation**: Include logging, metrics, and tracing in services

## Code Completion Checklist

Before considering any code complete, ensure it meets all the criteria in this checklist. This applies to both human-written and AI-generated code.

### Functionality

- [ ] **Core Functionality**: Code fulfills all requirements and acceptance criteria
- [ ] **Edge Cases**: All identified edge cases are handled appropriately
- [ ] **Error Handling**: All possible errors are caught and handled gracefully
- [ ] **Performance**: Code performs efficiently with expected data volumes
- [ ] **Accessibility**: User-facing components meet accessibility requirements

### Quality

- [ ] **Tests Written**: Unit tests cover all code paths and edge cases
- [ ] **Tests Passing**: All tests pass and provide good coverage (80%+)
- [ ] **No Linting Issues**: Code passes all linting checks (flake8, pylint)
- [ ] **Type Checking**: Type annotations are complete and pass mypy checks
- [ ] **Security**: Code is free from security vulnerabilities

### Documentation

- [ ] **Docstrings**: All public functions, classes, and methods have docstrings
- [ ] **Type Hints**: All function parameters and return values have type hints
- [ ] **Comments**: Complex logic has explanatory comments
- [ ] **README Updates**: Project documentation is updated if needed
- [ ] **API Documentation**: API endpoints are documented if applicable

### Review

- [ ] **Self-Review**: Code has been reviewed by the author/AI assistant
- [ ] **Peer Review**: Code has been reviewed by at least one other developer
- [ ] **No TODOs**: All TODOs are addressed or converted to tickets
- [ ] **No Debug Code**: All debugging print statements and commented-out code removed

### Integration

- [ ] **Dependency Management**: All dependencies are correctly specified
- [ ] **Configuration**: Any new configuration options are documented
- [ ] **Backward Compatibility**: Changes maintain backward compatibility
- [ ] **Service Integration**: Code integrates correctly with other services

### AI-Specific Checks

- [ ] **No Hard-coded Values**: All magic numbers and strings are properly defined as constants
- [ ] **Complete Implementation**: AI hasn't skipped implementation details with comments like "..."
- [ ] **Realistic Error Handling**: Error cases have specific, not generic, handling
- [ ] **Logic Verification**: All business logic has been verified by a human
- [ ] **Hallucination Check**: AI-provided information has been fact-checked

### Final Verification

- [ ] **Clean Build**: Code builds without warnings
- [ ] **Integration Tests**: Changes pass integration tests
- [ ] **No Regression**: Changes don't break existing functionality
- [ ] **Documentation Generation**: Documentation can be generated without errors
- [ ] **Final Manual Test**: Functionality has been manually verified if applicable

Use this checklist as part of your code review process. Code is only considered complete when all applicable items are checked off. For smaller changes, some items may be marked as "N/A" (not applicable).

By following these guidelines, we'll create maintainable, testable code while leveraging AI assistance effectively for the Peri project.
