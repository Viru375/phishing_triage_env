FROM python:3.10-slim

WORKDIR /app

# Copy and install dependencies first for Docker layer caching efficiency.
# Why: Installing deps before copying source means rebuilds skip this step
# unless requirements.txt actually changes, saving significant build time.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source files
COPY models.py .
COPY server/ ./server/
COPY inference.py .
COPY openenv.yaml .

# ── Environment Variable Defaults ─────────────────────────────────────────────
# These can be overridden at container runtime:
# e.g., docker run -e HF_TOKEN=... -e MODEL_NAME=... <image>
ENV API_BASE_URL="http://localhost:7860/v1"
ENV MODEL_NAME="saas-invoice-env"
ENV HF_TOKEN="sk-no-key-required"

# Expose port 7860 (Hugging Face Spaces standard)
EXPOSE 7860

# Start the FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
