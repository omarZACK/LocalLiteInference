# Dockerfile for LiteLLM SDK client using a slim Python base image
# -------------------------------------------------------------
# Builds a minimal container that installs the Python `litellm` SDK
# and runs the client script to communicate with an Ollama model (or
# other HuggingFace endpoints) via the SDK.
# -------------------------------------------------------------

FROM python:3.11-slim

# Install required Python packages (litellm SDK, python-dotenv, requests)
RUN pip install --no-cache-dir litellm python-dotenv requests

# Create a non‑root user for better security (optional but recommended)
RUN useradd -m -s /bin/bash appuser

# Set the working directory
WORKDIR /app

# Copy the project files needed at runtime
COPY scripts/ ./scripts/
COPY .env .

# Switch to the non‑root user
USER appuser

# Default command runs the client module (can be overridden)
CMD ["python", "-m", "scripts.litellm_client"]
