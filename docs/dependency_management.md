# Dependency Management Strategy

This document outlines the strategy for managing dependencies in the Peri TTS Python services. It provides guidelines for selecting, versioning, and maintaining dependencies to ensure a stable, secure, and maintainable codebase.

## Dependency Management Principles

### Core Principles

1. **Explicit Dependencies**: All dependencies must be explicitly declared
2. **Minimum Viable Dependencies**: Use the smallest set of dependencies necessary
3. **Version Pinning**: Pin dependency versions for reproducible builds
4. **Regular Updates**: Keep dependencies updated to address security issues
5. **Vulnerability Scanning**: Regularly scan for security vulnerabilities

## Dependency Declaration

### Requirements Files

The Peri TTS services use multiple requirements files for different purposes:

```
/peritest/python/
├── requirements.txt         # Core production dependencies
├── requirements-dev.txt     # Development dependencies
└── requirements-test.txt    # Testing dependencies
```

#### requirements.txt

Core production dependencies with pinned versions:

```
# Web Framework
fastapi==0.103.1             # Modern, fast web framework
uvicorn==0.23.2              # ASGI server
pydantic==2.3.0              # Data validation and settings management

# API and HTTP
python-multipart==0.0.6      # Multipart form parser
httpx==0.24.1                # HTTP client

# TTS Dependencies
kokoro==0.10.0               # Kokoro TTS engine
soundfile==0.12.1            # Audio file reading/writing
numpy==1.25.2                # Numerical operations
requests==2.31.0             # HTTP requests

# Utilities
python-dotenv==1.0.0         # Environment variable loading
pyyaml==6.0.1                # YAML parsing
tenacity==8.2.3              # Retry logic
structlog==23.1.0            # Structured logging
```

#### requirements-dev.txt

Dependencies for development:

```
# Include production dependencies
-r requirements.txt

# Development Tools
black==23.7.0                # Code formatting
isort==5.12.0                # Import sorting
flake8==6.1.0                # Linting
mypy==1.5.1                  # Type checking
pre-commit==3.3.3            # Pre-commit hooks

# Documentation
sphinx==7.1.2                # Documentation generator
sphinx-rtd-theme==1.2.2      # Sphinx theme
```

#### requirements-test.txt

Dependencies for testing:

```
# Include development dependencies
-r requirements-dev.txt

# Testing
pytest==7.4.0                # Testing framework
pytest-asyncio==0.21.1       # Async testing support
pytest-cov==4.1.0            # Coverage reporting
pytest-mock==3.11.1          # Mocking support
httpx==0.24.1                # HTTP client for API testing
```

### Dependency Groups

Group dependencies by purpose in the requirements files:

```
# Core Framework
fastapi==0.103.1
uvicorn==0.23.2
pydantic==2.3.0

# Audio Processing
soundfile==0.12.1
numpy==1.25.2

# TTS Engines
kokoro==0.10.0
# Add other TTS engines here
```

## Version Pinning Strategy

### Pinning Approach

The Peri TTS services use the following version pinning approach:

1. **Direct Dependencies**: Pin to exact versions (`==`)
2. **Transitive Dependencies**: Lock with pip-compile

Example using pip-compile:

```bash
# Install pip-tools
pip install pip-tools

# Generate compiled requirements
pip-compile requirements.in --output-file requirements.txt
pip-compile requirements-dev.in --output-file requirements-dev.txt
pip-compile requirements-test.in --output-file requirements-test.txt

# Update dependencies
pip-compile --upgrade requirements.in --output-file requirements.txt
```

### Version Selection Guidelines

Follow these guidelines when selecting dependency versions:

1. **Stability**: Prefer stable, well-established versions
2. **Security**: Avoid versions with known vulnerabilities
3. **Compatibility**: Ensure compatibility with other dependencies
4. **Features**: Select versions that provide needed features
5. **Performance**: Consider performance implications

## Dependency Isolation

### Virtual Environments

Always use virtual environments for dependency isolation:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Containerization

Use Docker for complete environment isolation:

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Large Dependencies Management

### TTS Models and Voices

TTS models and voices are large files that should be managed separately:

1. **Separate Repository**: Store models and voices in a separate repository
2. **Versioned Assets**: Version these assets independently
3. **On-Demand Download**: Download models and voices on demand
4. **Caching**: Cache models and voices to avoid repeated downloads

Example model downloader:

```python
import os
import requests
import hashlib
from tqdm import tqdm
from pathlib import Path
from typing import Dict, Optional

class ModelManager:
    """Manager for TTS models and voices."""
    
    def __init__(
        self,
        models_dir: str,
        voices_dir: str,
        catalog_url: str,
        cache_dir: Optional[str] = None
    ):
        """Initialize the model manager."""
        self.models_dir = Path(models_dir)
        self.voices_dir = Path(voices_dir)
        self.catalog_url = catalog_url
        self.cache_dir = Path(cache_dir) if cache_dir else None
        
        # Create directories if they don't exist
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
        # Load catalog
        self.catalog = self._load_catalog()
        
    def _load_catalog(self) -> Dict:
        """Load the model and voice catalog."""
        response = requests.get(self.catalog_url)
        response.raise_for_status()
        return response.json()
        
    def download_model(self, model_id: str) -> Path:
        """Download a model if it doesn't exist locally."""
        if model_id not in self.catalog["models"]:
            raise ValueError(f"Model '{model_id}' not found in catalog")
            
        model_info = self.catalog["models"][model_id]
        model_path = self.models_dir / f"{model_id}.bin"
        
        # Check if model already exists and has correct hash
        if model_path.exists():
            if self._verify_file_hash(model_path, model_info["hash"]):
                return model_path
            else:
                # Hash mismatch, redownload
                model_path.unlink()
                
        # Download model
        return self._download_file(
            url=model_info["url"],
            path=model_path,
            file_hash=model_info["hash"],
            description=f"Downloading model {model_id}"
        )
        
    def download_voice(self, voice_id: str) -> Path:
        """Download a voice if it doesn't exist locally."""
        if voice_id not in self.catalog["voices"]:
            raise ValueError(f"Voice '{voice_id}' not found in catalog")
            
        voice_info = self.catalog["voices"][voice_id]
        voice_path = self.voices_dir / f"{voice_id}.bin"
        
        # Check if voice already exists and has correct hash
        if voice_path.exists():
            if self._verify_file_hash(voice_path, voice_info["hash"]):
                return voice_path
            else:
                # Hash mismatch, redownload
                voice_path.unlink()
                
        # Download voice
        return self._download_file(
            url=voice_info["url"],
            path=voice_path,
            file_hash=voice_info["hash"],
            description=f"Downloading voice {voice_id}"
        )
        
    def _download_file(
        self,
        url: str,
        path: Path,
        file_hash: str,
        description: str
    ) -> Path:
        """Download a file with progress bar and hash verification."""
        # Create temporary file path
        temp_path = path.with_suffix(path.suffix + ".tmp")
        
        # Download file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get file size
        file_size = int(response.headers.get("content-length", 0))
        
        # Download with progress bar
        with tqdm(
            total=file_size,
            unit="B",
            unit_scale=True,
            desc=description
        ) as progress_bar:
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))
                        
        # Verify hash
        if not self._verify_file_hash(temp_path, file_hash):
            temp_path.unlink()
            raise ValueError(f"Hash mismatch for downloaded file: {path}")
            
        # Rename temporary file to final path
        temp_path.rename(path)
        return path
        
    def _verify_file_hash(self, path: Path, expected_hash: str) -> bool:
        """Verify the hash of a file."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
                
        calculated_hash = hasher.hexdigest()
        return calculated_hash == expected_hash
```

## Dependency Updating

### Update Schedule

Follow this update schedule for dependencies:

1. **Security Updates**: Apply immediately
2. **Minor Updates**: Apply monthly
3. **Major Updates**: Apply quarterly with thorough testing

### Update Process

Use this process for updating dependencies:

1. **Create Update Branch**: Create a dedicated branch for updates
2. **Update Dependencies**: Update dependencies in the requirements files
3. **Run Tests**: Run all tests to verify compatibility
4. **Create Pull Request**: Create a pull request for review
5. **Deploy to Staging**: Deploy to staging environment for testing
6. **Merge to Main**: Merge to main branch after approval

Example update script:

```python
#!/usr/bin/env python
"""Update dependencies in requirements files."""
import subprocess
import sys
from pathlib import Path

def update_requirements() -> None:
    """Update all requirements files."""
    # Get the requirements files
    req_files = [
        "requirements.in",
        "requirements-dev.in",
        "requirements-test.in"
    ]
    
    # Update each requirements file
    for req_file in req_files:
        input_file = Path(req_file)
        output_file = input_file.with_suffix(".txt")
        
        print(f"Updating {output_file}...")
        result = subprocess.run(
            [
                "pip-compile",
                "--upgrade",
                "--output-file",
                str(output_file),
                str(input_file)
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error updating {output_file}:")
            print(result.stderr)
            sys.exit(1)
            
        print(f"Updated {output_file}")
        
    print("All requirements files updated successfully")
    
if __name__ == "__main__":
    update_requirements()
```

## Dependency Security

### Vulnerability Scanning

Integrate vulnerability scanning into the CI/CD pipeline:

```yaml
# GitHub Actions workflow for vulnerability scanning
name: Dependency Security Scan

on:
  schedule:
    - cron: '0 0 * * *'  # Run daily
  push:
    paths:
      - 'requirements*.txt'
      - 'requirements*.in'

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install safety
        run: pip install safety
        
      - name: Run safety check
        run: safety check -r requirements.txt --full-report
        
      - name: Run Snyk
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high
```

### Audit Process

Follow this audit process for dependencies:

1. **Regular Scans**: Run vulnerability scans daily
2. **Review Reports**: Review vulnerability reports regularly
3. **Risk Assessment**: Assess the risk of each vulnerability
4. **Action Plan**: Create an action plan for addressing vulnerabilities
5. **Update Dependencies**: Update dependencies to fix vulnerabilities
6. **Verify Fixes**: Verify that vulnerabilities are fixed

## GitHub Dependabot Configuration

Use GitHub Dependabot to automate dependency updates:

```yaml
# .github/dependabot.yml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    allow:
      # Allow both direct and indirect updates for all packages
      - dependency-type: "all"
    commit-message:
      prefix: "pip"
      include: "scope"
    labels:
      - "dependencies"
      - "python"
    # Group updates together
    groups:
      development-dependencies:
        patterns:
          - "black"
          - "flake8"
          - "isort"
          - "mypy"
          - "pytest*"
      production-dependencies:
        patterns:
          - "fastapi"
          - "pydantic"
          - "uvicorn"
    # Ignore certain updates
    ignore:
      # Ignore major updates to libraries that require significant refactoring
      - dependency-name: "pydantic"
        update-types: ["version-update:semver-major"]
        
  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "monthly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "github-actions"
```

## Local Development Workflow

### Managing Development Dependencies

Use these commands for managing development dependencies:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Add a new development dependency
pip install black
pip freeze | grep black >> requirements-dev.in
pip-compile requirements-dev.in --output-file requirements-dev.txt
```

### Virtual Environment Best Practices

Follow these best practices for virtual environments:

1. **One Environment Per Project**: Create a separate environment for each project
2. **Version Control .gitignore**: Add venv directories to .gitignore
3. **Document Activation**: Document environment activation in README
4. **Deactivate When Switching**: Deactivate before switching projects
5. **Recreate Periodically**: Recreate environments periodically for clean state

## Managing Python Version Dependencies

### Python Version Specification

Specify Python version requirements:

```python
# pyproject.toml
[project]
requires-python = ">=3.8,<3.11"
```

```bash
# .python-version
3.10.8
```

### Python Version Compatibility

Ensure compatibility with supported Python versions:

1. **CI Testing**: Test with all supported Python versions in CI
2. **Use Feature Detection**: Use feature detection instead of version checks
3. **Document Compatibility**: Document Python version requirements
4. **Consider Minimum Version**: Set minimum version based on required features

Example CI configuration for Python version testing:

```yaml
# GitHub Actions workflow for Python version testing
name: Python Version Compatibility

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-test.txt
          
      - name: Run tests
        run: pytest
```

## System Dependencies

### Identifying System Dependencies

The Peri TTS services depend on these system packages:

1. **espeak-ng**: Required for Kokoro TTS phoneme generation
2. **libsndfile**: Required for audio file processing
3. **ffmpeg**: Required for audio format conversion (optional)

### Documenting System Dependencies

Document system dependencies in the README:

```markdown
## System Dependencies

The Peri TTS services require the following system dependencies:

- **espeak-ng**: Text-to-phoneme conversion for TTS
  - Windows: [Download installer](https://github.com/espeak-ng/espeak-ng/releases)
  - macOS: `brew install espeak-ng`
  - Ubuntu/Debian: `apt-get install espeak-ng`

- **libsndfile**: Audio file processing
  - Windows: Included with Python soundfile package
  - macOS: `brew install libsndfile`
  - Ubuntu/Debian: `apt-get install libsndfile1`

- **ffmpeg** (optional): Audio format conversion
  - Windows: [Download installer](https://ffmpeg.org/download.html)
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `apt-get install ffmpeg`
```

### Docker System Dependencies

Include system dependencies in Dockerfile:

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Rest of Dockerfile...
```

## Legacy Dependencies

### Handling Legacy Dependencies

Follow these guidelines for legacy dependencies:

1. **Document Workarounds**: Document any workarounds for legacy dependencies
2. **Plan Migration**: Create a plan for migrating away from legacy dependencies
3. **Isolate Impact**: Isolate legacy dependencies to minimize their impact
4. **Test Thoroughly**: Test legacy dependencies thoroughly to understand behavior

### Example Adapter Pattern

Use the adapter pattern to isolate legacy dependencies:

```python
from typing import Protocol, Dict, Any

class TTSEngine(Protocol):
    """Interface for TTS engines."""
    
    def generate_speech(self, text: str, voice_id: str, options: Dict[str, Any]) -> bytes:
        """Generate speech from text."""
        ...

class LegacyTTSAdapter:
    """Adapter for legacy TTS engine."""
    
    def __init__(self, legacy_engine):
        """Initialize the adapter."""
        self.legacy_engine = legacy_engine
        
    def generate_speech(self, text: str, voice_id: str, options: Dict[str, Any]) -> bytes:
        """Generate speech from text using the legacy engine."""
        # Convert parameters to legacy format
        legacy_options = {
            "rate": options.get("speed", 1.0) * 100,
            "pitch": options.get("pitch", 1.0) * 50,
            "voice": self._map_voice(voice_id)
        }
        
        # Call legacy engine
        legacy_audio = self.legacy_engine.text_to_speech(
            text=text,
            **legacy_options
        )
        
        # Convert legacy audio format if needed
        return self._convert_audio(legacy_audio)
        
    def _map_voice(self, voice_id: str) -> str:
        """Map modern voice ID to legacy voice name."""
        voice_mapping = {
            "am_adam": "male1",
            "am_emma": "female1",
            # Add more mappings
        }
        return voice_mapping.get(voice_id, "default")
        
    def _convert_audio(self, legacy_audio) -> bytes:
        """Convert legacy audio format to modern format."""
        # Conversion logic
        return legacy_audio
```

## Appendix: Dependency Review Checklist

Use this checklist when reviewing new dependencies:

- [ ] **Necessity**: Is this dependency really needed?
- [ ] **License**: Is the license compatible with our project?
- [ ] **Maintenance**: Is the dependency actively maintained?
- [ ] **Security**: Does the dependency have security vulnerabilities?
- [ ] **Size**: What is the size impact of the dependency?
- [ ] **Performance**: What is the performance impact of the dependency?
- [ ] **Compatibility**: Is the dependency compatible with our existing stack?
- [ ] **Documentation**: Is the dependency well-documented?
- [ ] **Community**: Does the dependency have a healthy community?
- [ ] **Testing**: Is the dependency well-tested?

This comprehensive dependency management strategy ensures that the Peri TTS services are built on a stable, secure, and maintainable foundation.
