# ─────────────────────────────────────────────────────────────
# Financial Advisor Chatbot — Multi-stage Dockerfile
# ─────────────────────────────────────────────────────────────
# Multi-stage build for smaller production image
# Stage 1: Install dependencies
# Stage 2: Copy app code (keeps layer cache efficient)
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies first (layer caching optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────────────────────
# Production stage
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Security: run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY .env.example ./

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Run Streamlit in production mode
ENTRYPOINT ["streamlit", "run", "app/main.py", \
    "--server.port=8501", \
    "--server.headless=true", \
    "--server.fileWatcherType=none", \
    "--browser.gatherUsageStats=false", \
    "--server.maxUploadSize=1"]
