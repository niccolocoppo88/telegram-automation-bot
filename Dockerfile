# SPDX-License-Identifier: MIT
# Telegram Automation Bot — Dockerfile

FROM python:3.11-slim AS builder

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies for some packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage — slim runtime image
FROM python:3.11-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 botgroup && \
    useradd --uid 1000 --gid botgroup --shell /bin/bash botuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/botuser/.local

# Copy application source
COPY --chown=botuser:botgroup src/ ./src/
COPY --chown=botuser:botgroup config.py ./
COPY --chown=botuser:botgroup .env.example .env

# Create data directory with correct permissions
RUN mkdir -p /app/data && chown botuser:botgroup /app/data

# Expose ports
EXPOSE 8000 8080

# Volume for persistent data
VOLUME ["/app/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER botuser

# Set PATH for installed packages
ENV PATH=/home/botuser/.local/bin:$PATH

# Run with uvicorn (FastAPI for webhooks + health)
CMD ["sh", "-c", "uvicorn src.api:app --host 0.0.0.0 --port 8000 & python src/bot.py"]