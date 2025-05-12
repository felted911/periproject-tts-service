# Testing Architecture for Peri TTS Services

This document outlines the testing architecture for the Python-based TTS services in the Peri project. It defines a comprehensive approach to ensure code quality, functionality, and performance through automated testing at multiple levels.

## Testing Pyramid

The Peri TTS services follow a testing pyramid approach with the following layers:

1. **Unit Tests**: Testing individual components in isolation
2. **Integration Tests**: Testing interactions between components
3. **API Tests**: Testing the HTTP API endpoints
4. **Performance Tests**: Testing system performance under load
5. **End-to-End Tests**: Testing complete functionality from request to audio generation

The distribution of tests should follow this approximate ratio:
- 70% Unit Tests
- 20% Integration Tests
- 5% API Tests
- 3% Performance Tests
- 2% End-to-End Tests

## Test Environments

### Local Development Environment
- Used for rapid feedback during development
- Runs unit tests and selected integration tests
- Utilizes small voice models for quick testing

### CI Environment
- Runs all tests automatically on each commit
- Uses containerized environment matching production
- Tests with full voice models for accuracy

### Staging Environment
- Mirrors production configuration
- Used for performance testing and final validation
- Runs end-to-end tests against deployed services

## Test Categories

### Unit Tests

Unit tests focus on testing individual components in isolation:

```python
class TestKokoroProvider:
    def setup_method(self):
        # Mock dependencies
        self.mock_pipeline = mock.MagicMock()
        self.provider = KokoroTTSProvider(
            model_provider=lambda: self.mock_pipeline,
            voices_dir="/mock/voices"
        )
    
    def test_get_voices(self):
        # Arrange
        self.mock_pipeline.list_voices.return_value = ["voice1", "voice2"]
        
        # Act
        voices = self.provider.get_voices()
        
        # Assert
        assert len(voices) == 2
        assert voices[0].id == "voice1"
```

### Integration Tests

Integration tests verify the interaction between components:

```python
class TestTTSServiceWithKokoro:
    def setup_method(self):
        # Set up actual components, not mocks
        self.cache = CacheManager(cache_dir=tempfile.mkdtemp())
        self.provider = KokoroTTSProvider(
            model_path=TEST_MODEL_PATH,
            voices_dir=TEST_VOICES_DIR,
            cache_dir=self.cache.cache_dir
        )
        self.service = TTSService(
            providers={"kokoro": self.provider},
            cache=self.cache
        )
    
    def test_generate_speech_with_caching(self):
        # First request should generate audio
        result1 = self.service.generate_speech("Hello world", "test_voice")
        
        # Second request should use cache
        with mock.patch.object(self.provider, 'generate_speech') as mock_gen:
            result2 = self.service.generate_speech("Hello world", "test_voice")
            mock_gen.assert_not_called()  # Should not call generate again
            
        assert result1.audio_data == result2.audio_data
```

### API Tests

API tests verify the HTTP endpoints and request/response formats:

```python
class TestTTSAPI:
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_generate_speech_endpoint(self):
        # Arrange
        request_data = {
            "text": "Hello world",
            "voice": "test_voice",
            "speed": 1.0
        }
        
        # Act
        response = self.client.post("/tts", json=request_data)
        
        # Assert
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "audio/wav"
        # Validate audio data
```

### Performance Tests

Performance tests measure system behavior under various loads:

```python
class TestTTSPerformance:
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_concurrent_requests(self):
        # Arrange
        request_data = {
            "text": "Hello world",
            "voice": "test_voice"
        }
        
        # Act
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self.client.post, "/tts", json=request_data)
                for _ in range(20)
            ]
            responses = [f.result() for f in futures]
        end_time = time.time()
        
        # Assert
        assert all(r.status_code == 200 for r in responses)
        assert end_time - start_time < 30  # Max 30 seconds for 20 requests
```

### End-to-End Tests

End-to-End tests validate the complete system functionality:

```python
class TestTTSEndToEnd:
    def setup_method(self):
        # Use deployed service or start services
        self.base_url = "http://localhost:8000"
    
    def test_complete_workflow(self):
        # Get available voices
        voices_response = requests.get(f"{self.base_url}/voices")
        assert voices_response.status_code == 200
        voices = voices_response.json()["voices"]
        
        # Generate speech
        voice_id = voices[0]["id"]
        tts_response = requests.post(
            f"{self.base_url}/tts",
            json={"text": "End to end test", "voice": voice_id},
            headers={"Accept": "audio/wav"}
        )
        assert tts_response.status_code == 200
        
        # Validate audio file
        audio_data = tts_response.content
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp:
            temp.write(audio_data)
            temp.flush()
            # Verify audio file properties
            audio = wave.open(temp.name, "rb")
            assert audio.getnchannels() == 1  # Mono audio
            assert audio.getframerate() > 0   # Valid sample rate
```

## Test Data Management

### Test Voice Models

- Maintain small test voice models for unit and integration tests
- Store test models in a dedicated repository
- Version test models to ensure reproducible tests

### Test Text Corpus

- Create a diverse corpus of test texts for different languages
- Include edge cases like numbers, abbreviations, and special characters
- Maintain reference outputs for key test cases

## Mock Strategy

### External Dependencies

- Mock all external services and APIs
- Use dependency injection to replace real services with mocks
- Create realistic mock responses based on real service behavior

### Heavy Components

- Mock computationally intensive components in unit tests
- Use lightweight implementations for integration tests
- Reserve full implementations for end-to-end tests

## Test Coverage

### Coverage Goals

- 90%+ line coverage for core service and provider code
- 80%+ line coverage for API and infrastructure code
- 100% coverage for critical error handling paths

### Coverage Tracking

- Track coverage as part of CI pipeline
- Generate coverage reports for each build
- Block merges if coverage drops below thresholds

## Test Automation

### Test Runners

- Use pytest as the primary test runner
- Organize tests with fixtures and parametrization
- Use pytest-cov for coverage reporting

### Test Selection

- Run fast tests on every commit
- Run full test suite before merging to main branches
- Run performance tests on a schedule

## Testing for Specific Concerns

### Security Testing

- Test input validation and sanitization
- Verify authentication and authorization
- Check for common vulnerabilities

### Accessibility Testing

- Verify audio format compatibility with assistive technologies
- Test with screen readers and other accessibility tools
- Ensure compliance with accessibility standards

### Internationalization Testing

- Test with texts in multiple languages
- Verify correct handling of non-ASCII characters
- Test voice selection logic for different languages

## Continuous Improvement

### Test Metrics

- Track test execution time
- Monitor test stability and flakiness
- Measure coverage trends over time

### Testing Feedback Loop

- Use test results to guide development
- Regular reviews of test quality and coverage
- Update tests based on bug reports and user feedback

This testing architecture ensures a comprehensive approach to quality assurance for the Peri TTS services, balancing thorough testing with practical considerations for development velocity.
