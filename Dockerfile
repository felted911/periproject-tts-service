FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Create required directories
RUN mkdir -p data/voices data/cache

# Set Python path
ENV PYTHONPATH=/app

# Set environment variables
ENV ENVIRONMENT=production
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV LOG_LEVEL=INFO
ENV KOKORO_USE_GPU=false

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "src/main.py"]
