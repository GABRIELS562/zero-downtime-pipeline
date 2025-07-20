# Multi-stage Dockerfile for Finance Trading Application
# Optimized for production with minimal image size and security

# Stage 1: Base Python image with system dependencies
FROM python:3.11-slim as base

# Set build arguments
ARG BUILD_ID
ARG GIT_COMMIT
ARG BUILD_TIMESTAMP

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r trading && useradd -r -g trading trading

# Set work directory
WORKDIR /app

# Stage 2: Dependencies installation
FROM base as dependencies

# Install Python dependencies
COPY requirements-simple.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Development image
FROM dependencies as development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Change ownership to trading user
RUN chown -R trading:trading /app

# Switch to non-root user
USER trading

# Expose port
EXPOSE 8000

# Development command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# Stage 4: Production builder
FROM dependencies as builder

# Copy only necessary files for building
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY requirements-simple.txt ./requirements.txt

# Create optimized Python cache
RUN python -m compileall src/

# Stage 5: Production image
FROM python:3.11-slim as production

# Set build arguments
ARG BUILD_ID
ARG GIT_COMMIT
ARG BUILD_TIMESTAMP

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    APP_ENV=production \
    LOG_LEVEL=info \
    WORKERS=4 \
    BUILD_ID=${BUILD_ID} \
    GIT_COMMIT=${GIT_COMMIT} \
    BUILD_TIMESTAMP=${BUILD_TIMESTAMP}

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r trading && useradd -r -g trading trading

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app/src ./src
COPY --from=builder /app/scripts ./scripts
COPY --from=builder /app/requirements.txt .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R trading:trading /app

# Switch to non-root user
USER trading

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Forensic metadata labels
LABEL forensic.build_id=${BUILD_ID} \
      forensic.git_commit=${GIT_COMMIT} \
      forensic.build_timestamp=${BUILD_TIMESTAMP} \
      forensic.compliance=SOX \
      forensic.application=finance-trading \
      forensic.security_scan=required

# Production command
CMD ["gunicorn", "src.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "5", "--log-level", "info"]

# Stage 6: Testing image
FROM development as testing

# Install testing dependencies
COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt

# Copy test files
COPY tests/ ./tests/
COPY pytest.ini .
COPY .coverage.ini .

# Run tests
CMD ["pytest", "-v", "--cov=src", "--cov-report=html", "--cov-report=term"]

# Stage 7: Database migration image
FROM dependencies as migrations

# Copy migration scripts
COPY src/database/ ./src/database/
COPY scripts/init_database.py ./scripts/
COPY alembic.ini .

# Switch to non-root user
USER trading

# Migration command
CMD ["python", "-m", "alembic", "upgrade", "head"]