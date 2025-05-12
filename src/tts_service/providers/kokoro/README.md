# Kokoro TTS Provider

This module contains a refactored implementation of the Kokoro TTS provider, adhering to the project's coding guidelines and architectural principles.

## Structure

The provider has been decomposed into several smaller, focused classes:

1. `KokoroTTSProvider` (in `provider.py`): Main coordinator class that implements the `TTSProvider` interface and coordinates the other components.

2. `KokoroVoiceManager` (in `voice_manager.py`): Manages voice and language information, including loading and retrieving voices and languages.

3. `KokoroModelHandler` (in `model_handler.py`): Handles model initialization and management, including loading the Kokoro model and checking availability.

4. `KokoroAudioGenerator` (in `audio_generator.py`): Responsible for generating audio using the Kokoro model, including converting audio formats.

5. Protocol interfaces (in `protocols.py`): Defines the interfaces for the different components, ensuring loose coupling and clear responsibilities.

## Usage

To use the Kokoro TTS provider, you only need to import and instantiate the `KokoroTTSProvider` class:

```python
from tts_service.providers import KokoroTTSProvider

# Create provider instance
provider = KokoroTTSProvider()

# Initialize provider
await provider.initialize()

# Generate speech
result = await provider.generate_speech("Hello, world!", "af_heart")
```

## Refactoring Rationale

This refactoring addresses the "Large Classes" guideline violation by:

1. Splitting the original 350+ line class into multiple smaller, focused classes:
   - The voice management logic is now in `KokoroVoiceManager`
   - The model handling logic is now in `KokoroModelHandler`
   - The audio generation logic is now in `KokoroAudioGenerator`

2. Improving maintainability through:
   - Clear separation of concerns
   - Reduced method sizes
   - Protocol interfaces for better testability and looser coupling

3. Ensuring backward compatibility by maintaining the same interface as the original provider.

## Benefits

- **Improved Testability**: Each component can be tested independently
- **Clearer Responsibilities**: Each class has a single, clear purpose
- **Reduced Complexity**: Methods are shorter and more focused
- **Better Maintainability**: The code is more organized and easier to understand
- **Dependency Injection**: Components are injected, making mocking easier for testing
