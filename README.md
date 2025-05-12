# Peri TTS Service

This service provides Text-to-Speech (TTS) capabilities for the Peri morning routine assistant using the Kokoro TTS engine.

## Overview

The Peri TTS Service is designed to provide high-quality text-to-speech conversion with the following features:

- Multiple voice options with natural-sounding speech
- Efficient caching for improved performance
- RESTful API with comprehensive error handling
- Extensive logging and monitoring

## Quick Start

### Installation and Running (Automatic)

Use the provided script to install dependencies, download models, and start the service:

```bash
# Windows
install_and_run.bat

# Linux/macOS
chmod +x install_and_run.sh
./install_and_run.sh
```

### Manual Installation

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Download the required model and voice files:

```bash
python -m src.utils.download_models --model-type int8
```

For GPU acceleration, use:
```bash
python -m src.utils.download_models --model-type fp16
```

### Optional: Install External Dependencies

For full audio format support (MP3 and OGG), install FFmpeg:

* **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your PATH
* **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
* **macOS**: `brew install ffmpeg`

### Running the Service Manually

From the root directory, run:

```bash
cd src
python main.py
```

The service will be available at http://localhost:8000 by default.

### API Documentation

API documentation is available at:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API Endpoints

### TTS Generation

```http
POST /api/v1/tts
```

Request body:

```json
{
  "text": "Hello, this is a test message.",
  "voice": "af_heart",
  "options": {
    "speed": 1.0,
    "language": "en-us"
  },
  "format": "wav"
}
```

**Note**: Without FFmpeg installed, only WAV format is supported.

### Voice Listing

```http
GET /api/v1/voices
```

### Language Listing

```http
GET /api/v1/languages
```

### Provider Information

```http
GET /api/v1/providers
```

## Project Structure

```
python/
├── config/                  # Configuration files
├── data/                    # Data storage
│   ├── cache/               # Audio cache
│   ├── models/              # Model files
│   └── voices/              # Voice files
├── src/                     # Source code
│   ├── tts_service/         # Main package
│   │   ├── api/             # API layer
│   │   ├── infrastructure/  # Cross-cutting concerns
│   │   ├── models/          # Data models
│   │   ├── providers/       # TTS engines
│   │   └── services/        # Business logic
│   ├── utils/               # Utility scripts
│   │   └── download_models.py # Model downloader
│   └── main.py              # Application entry point
└── tests/                   # Tests
    ├── integration/         # Integration tests
    └── unit/                # Unit tests
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
flake8 src
```

## Deployment

**IMPORTANT**: This project is intended for development purposes only. The CI/CD pipeline is configured to deploy only to the development environment.

### Pushing to Git

1. Ensure all tests pass using `pytest`
2. Push your changes to the `develop` branch:

```bash
git checkout develop
git add .
git commit -m "Your commit message"
git push origin develop
```

3. The GitHub Actions workflow will automatically validate, test, build, and deploy to the development environment.

### CI/CD Configuration

The CI/CD pipeline is configured in `.github/workflows/dev-deploy.yml` and includes these stages:

1. Branch verification (ensures we're not deploying to production)
2. Code validation (linting and formatting)
3. Testing
4. Docker image build
5. Deployment to development environment

See the `.github/README.md` file for more details on the CI/CD configuration.

## Model Information

This service uses the Kokoro TTS model, which is available in multiple formats:

- **fp32**: Full precision model (largest, most accurate)
- **fp16**: Half precision model (balanced, good for GPU)
- **int8**: Quantized model (smallest, fastest on CPU)

By default, the service uses the int8 model for better performance. You can switch to the fp16 model for GPU acceleration or the fp32 model for maximum quality by setting the appropriate environment variables.

## Audio Format Support

The service supports the following audio formats:

- **WAV**: Fully supported (no external dependencies)
- **MP3**: Requires FFmpeg to be installed
- **OGG**: Requires FFmpeg to be installed

## Troubleshooting

### Common Issues

1. **Missing 'audioop' or 'pyaudiooop' module**: This is a common issue with audio processing in Python. For basic functionality (WAV format only), you don't need to install anything extra, as we've modified the code to work without these dependencies.

2. **Model download issues**: If you encounter issues downloading the model files, you can download them manually from the following URLs and place them in the appropriate directories:
   - INT8 Model: https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
   - Voices File: https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

3. **Missing dependencies**: If you encounter errors about missing dependencies, try reinstalling with:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **Port conflicts**: If port 8000 is already in use, change the port by setting the API_PORT environment variable:
   ```bash
   # Windows
   set API_PORT=8001
   
   # Linux/macOS
   export API_PORT=8001
   ```

## Environment Variables

The service can be configured using the following environment variables:

- `ENVIRONMENT`: Set to "development" or "production" (default: "development")
- `API_HOST`: Host to bind to (default: "0.0.0.0")
- `API_PORT`: Port to bind to (default: 8000)
- `KOKORO_USE_GPU`: Set to "true" to use GPU acceleration (default: "false")
- `LOG_LEVEL`: Logging level (default: "INFO")

## License

This project is licensed under the MIT License. The Kokoro TTS model is licensed under the Apache License 2.0.
