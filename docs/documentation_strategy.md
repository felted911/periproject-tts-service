# Documentation Strategy

This document outlines the documentation strategy for the Peri TTS Python services. It defines standards, processes, and tools for creating and maintaining comprehensive documentation for developers, users, and other stakeholders.

## Documentation Types

The Peri TTS services include the following types of documentation:

1. **API Documentation**: OpenAPI/Swagger documentation for REST APIs
2. **Code Documentation**: Docstrings and type hints in the codebase
3. **Technical Documentation**: Architecture, design decisions, and implementation details
4. **Developer Guides**: How-to guides for developers working on the project
5. **Operational Documentation**: Deployment, monitoring, and maintenance guides

## Documentation Tools and Technologies

### API Documentation

- **OpenAPI/Swagger**: FastAPI's built-in support for OpenAPI documentation
- **ReDoc**: Alternative view for OpenAPI documentation
- **Postman Collections**: For API testing and exploration

### Code Documentation

- **Google-style Docstrings**: Standard format for Python docstrings
- **Type Hints**: Python type annotations for static type checking
- **Sphinx**: Documentation generator for Python code
- **Doctest**: Executable examples in docstrings

### Technical Documentation

- **Markdown**: Primary format for technical documentation
- **PlantUML/Mermaid**: For diagrams and visual representations
- **GitHub Wiki/Pages**: For hosting documentation

## Documentation Standards

### API Documentation Standards

All API endpoints must include:

- Clear, concise descriptions
- Complete request and response schemas
- Example requests and responses
- Error responses and status codes
- Authentication requirements
- Rate limiting information

Example FastAPI endpoint with documentation:

```python
@router.post("/tts", response_class=StreamingResponse, tags=["TTS"])
async def generate_speech(
    request: TTSRequest,
    accept: str = Header("audio/wav"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> StreamingResponse:
    """
    Generate speech from text using the specified voice.
    
    The generated audio is returned as a streaming response in either WAV or MP3 format,
    depending on the Accept header.
    
    Parameters:
    - **request**: The TTS request containing text, voice, and options
    - **accept**: Audio format to return (audio/wav or audio/mpeg)
    
    Returns:
    - A streaming response with the generated audio
    
    Raises:
    - 400 BadRequest: If the request is invalid
    - 404 NotFound: If the requested voice is not found
    - 500 InternalServerError: If speech generation fails
    
    Example:
        ```
        curl -X POST "http://localhost:8000/tts" \\
          -H "Content-Type: application/json" \\
          -H "Accept: audio/wav" \\
          -d '{"text":"Hello world","voice":"en_female_1","speed":1.0}'
        ```
    """
    # Implementation...
```

### Code Documentation Standards

All code must adhere to these documentation standards:

#### Classes

- Purpose and responsibility
- Usage examples
- Constructor parameters
- Attributes
- Exceptions raised

Example:

```python
class KokoroTTSProvider:
    """
    Kokoro TTS implementation of the TTSProvider interface.
    
    This class wraps the Kokoro TTS library to provide text-to-speech services
    following the TTSProvider interface. It manages model loading, voice selection,
    and speech generation.
    
    Example:
        ```python
        provider = KokoroTTSProvider(model_path="./models", voices_dir="./voices")
        await provider.load_model("a")  # Load American English model
        voices = await provider.get_voices()
        audio = await provider.generate_speech("Hello world", voices[0].id)
        ```
    
    Attributes:
        model_path (str): Path to the Kokoro model files
        voices_dir (str): Path to the voice files
        current_model (Optional[KPipeline]): Currently loaded model, if any
    
    Raises:
        ModelNotFoundError: If the requested model cannot be found
        VoiceNotFoundError: If the requested voice cannot be found
        GenerationFailedError: If speech generation fails
    """
```

#### Functions/Methods

- Purpose
- Parameters
- Return value
- Exceptions raised
- Usage examples for complex functions

Example:

```python
async def generate_speech(
    self, text: str, voice_id: str, options: Dict[str, Any] = None
) -> AudioResult:
    """
    Generate speech for the given text using the specified voice.
    
    Args:
        text: The text to convert to speech
        voice_id: The ID of the voice to use
        options: Additional options for speech generation, including:
            - speed (float): Speech speed multiplier (0.5-2.0)
            - split_pattern (str): Regex pattern for splitting text
    
    Returns:
        An AudioResult containing the generated audio data and metadata
    
    Raises:
        ModelNotLoadedError: If no model is currently loaded
        VoiceNotFoundError: If the requested voice is not found
        GenerationFailedError: If speech generation fails
    
    Example:
        ```python
        audio_result = await provider.generate_speech(
            "Hello world",
            "am_adam",
            {"speed": 1.2}
        )
        with open("output.wav", "wb") as f:
            f.write(audio_result.audio_data)
        ```
    """
```

### Technical Documentation Standards

Technical documentation should:

- Be written in Markdown
- Include a clear title and introduction
- Use appropriate headings and subheadings
- Include diagrams for complex concepts
- Provide code examples where relevant
- Be reviewed and updated regularly

## Documentation Organization

The documentation is organized as follows:

```
/peritest/python/
├── README.md               # Project overview and quick start
├── docs/                   # Technical documentation
│   ├── architecture.md     # System architecture
│   ├── coding_guidelines.md# Coding standards
│   ├── testing_architecture.md # Testing approach
│   └── ...
├── app/                    # Application code with docstrings
├── tests/                  # Test cases and examples
└── api_docs/               # Generated API documentation
```

## Documentation Process

### Creation Process

1. **Documentation Planning**: Identify documentation needs at the start of each feature
2. **Documentation First**: Write API specifications before implementation
3. **Code Documentation**: Add docstrings and type hints during coding
4. **Technical Documentation**: Create/update technical docs after implementation
5. **Review**: Documentation review as part of the code review process

### Maintenance Process

1. **Version Tracking**: Documentation versioned with code in Git
2. **Regular Audits**: Quarterly review of documentation accuracy
3. **Update Triggers**: Documentation updates required for:
   - New features
   - API changes
   - Bug fixes that change behavior
   - Architecture changes

## Documentation Generation

### API Documentation Generation

FastAPI automatically generates OpenAPI documentation:

```python
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

app = FastAPI(
    title="Peri TTS API",
    description="Text-to-Speech API for the Peri project",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Peri TTS API",
        swagger_js_url="https://unpkg.com/swagger-ui-dist@4/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@4/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Peri TTS API",
    )
```

### Code Documentation Generation

Sphinx can be used to generate documentation from docstrings:

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Generate documentation
sphinx-apidoc -o docs/api app
cd docs
make html
```

The resulting HTML documentation will be in `docs/_build/html/`.

## Documentation Testing

### API Documentation Testing

- Validate OpenAPI schema against standards
- Ensure examples work as documented
- Test documentation with developers outside the team

### Code Documentation Testing

- Use doctest to test examples in docstrings
- Ensure type hints are compatible with mypy
- Check docstring coverage with tools like interrogate

## Documentation Review Checklist

All documentation should be reviewed against this checklist:

- [ ] Documentation is accurate and up-to-date
- [ ] Language is clear and concise
- [ ] Examples are correct and working
- [ ] All parameters, return values, and exceptions are documented
- [ ] Diagrams are clear and represent the current system
- [ ] Links to other documentation are working
- [ ] No confidential information is exposed

## Roles and Responsibilities

### Development Team

- Write and maintain code documentation
- Create API specifications
- Keep documentation updated as code changes

### Technical Writers (if available)

- Review and improve technical documentation
- Ensure consistency across documentation
- Create high-level guides and tutorials

### Project Leads

- Ensure documentation standards are followed
- Approve documentation for major releases
- Prioritize documentation tasks

## Tools and Automation

### Documentation Linting

- Use tools like pydocstyle to check docstring format
- Add documentation linting to CI pipeline

### Automated Checks

- Ensure docstrings present for public APIs
- Verify type hints are complete
- Check for broken links in documentation

### Documentation Generation in CI/CD

- Generate API documentation as part of the build process
- Deploy documentation to a static site for easy access

## Version Control and Changelog

### Documentation Versioning

- Documentation is versioned with the codebase
- Previous versions available for reference

### Changelog Management

- Keep a detailed changelog of API changes
- Include documentation updates in release notes

## Continuous Improvement

The documentation strategy should be reviewed and improved regularly:

- Gather feedback from users of the documentation
- Track common support questions to identify documentation gaps
- Update documentation standards based on best practices

This documentation strategy ensures that the Peri TTS Python services are well-documented, making them easier to use, maintain, and extend over time.
