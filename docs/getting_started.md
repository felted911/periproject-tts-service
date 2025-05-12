# Getting Started with Peri TTS Service

This guide will help you set up and run the Peri TTS Service on your local environment.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment tool (recommended)

## Setup

1. **Create a virtual environment:**

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Verify the installation:**

   ```bash
   python -c "import kokoro_tts; print('Kokoro TTS available' if hasattr(kokoro_tts, 'KokoroTTS') else 'Mock implementation will be used')"
   ```

## Running the Service

### Using Scripts

The repository includes convenience scripts for running the service:

- **Windows:**
  ```
  run_app.bat
  ```

- **Linux/macOS:**
  ```
  chmod +x run_app.sh
  ./run_app.sh
  ```

### Manual Starting

1. **Set the Python path:**

   ```bash
   # Windows
   set PYTHONPATH=%CD%
   
   # Linux/macOS
   export PYTHONPATH=$(pwd)
   ```

2. **Run the application:**

   ```bash
   cd src
   python main.py
   ```

3. **Access the API documentation:**

   Open your browser and navigate to:
   - http://localhost:8000/api/docs (Swagger UI)
   - http://localhost:8000/api/redoc (ReDoc)

## Testing

The service includes comprehensive tests to verify functionality.

### Using Scripts

Run all tests with the included scripts:

- **Windows:**
  ```
  run_tests.bat
  ```

- **Linux/macOS:**
  ```
  chmod +x run_tests.sh
  ./run_tests.sh
  ```

### Manual Testing

Run specific test categories:

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run with coverage report
pytest --cov=src/tts_service tests/
```

## Docker Deployment

The service can be run in Docker for easier deployment:

```bash
# Build and start the service
docker-compose up --build -d

# Check logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Using the API

### Basic Usage

1. **List available voices:**

   ```bash
   curl http://localhost:8000/api/v1/voices
   ```

2. **Generate speech:**

   ```bash
   curl -X POST http://localhost:8000/api/v1/tts \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, this is a test message.", "voice": "en_female_1", "options": {"speed": 1.0}, "format": "wav"}' \
     --output output.wav
   ```

### Example Python Client

Here's a simple Python client to interact with the API:

```python
import requests
import io
from pydub import AudioSegment
from pydub.playback import play

# API endpoint
base_url = "http://localhost:8000/api/v1"

# Get available voices
response = requests.get(f"{base_url}/voices")
voices = response.json()
print(f"Available voices: {list(voices.keys())}")

# Generate speech
tts_data = {
    "text": "Hello, this is a test message from the Peri TTS Service.",
    "voice": "en_female_1",
    "options": {"speed": 1.0},
    "format": "wav"
}

response = requests.post(f"{base_url}/tts", json=tts_data)

if response.status_code == 200:
    # Load audio data
    audio_data = io.BytesIO(response.content)
    audio = AudioSegment.from_wav(audio_data)
    
    # Save to file
    audio.export("output.wav", format="wav")
    print("Speech generated and saved to output.wav")
    
    # Play audio (optional)
    play(audio)
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   
   If port 8000 is already in use, change the port by setting the `API_PORT` environment variable.

2. **Missing dependencies:**

   Ensure all dependencies are installed: `pip install -r requirements.txt`

3. **Module not found errors:**

   Make sure the Python path is set correctly to include the project root.

### Logs

Check the application logs for detailed error information. In development mode, logs are output to the console.

## Next Steps

After setting up the service, you might want to:

1. Explore the API using the Swagger UI at http://localhost:8000/api/docs
2. Integrate the service with your Flutter application
3. Add custom voices to the `data/voices` directory
4. Explore advanced TTS options in the API documentation
