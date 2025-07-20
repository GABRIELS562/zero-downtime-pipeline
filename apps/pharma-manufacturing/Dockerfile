# Multi-stage Dockerfile for Pharmaceutical Manufacturing System
# Optimized for GMP compliance and FDA validation

# =============================================================================
# Base Stage - Common dependencies
# =============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for pharmaceutical manufacturing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1001 pharma && \
    useradd --uid 1001 --gid pharma --shell /bin/bash --create-home pharma

# Set working directory
WORKDIR /app

# =============================================================================
# Dependencies Stage - Install Python dependencies
# =============================================================================
FROM base as dependencies

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# =============================================================================
# Development Stage - For local development
# =============================================================================
FROM dependencies as development

# Install development dependencies
RUN pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy

# Copy source code
COPY --chown=pharma:pharma . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/backups && \
    chown -R pharma:pharma /app

USER pharma

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

# Development command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# Builder Stage - Compile and optimize
# =============================================================================
FROM dependencies as builder

# Copy source code
COPY . .

# Create optimized byte code
RUN python -m compileall src/

# =============================================================================
# Production Stage - Optimized for production deployment
# =============================================================================
FROM base as production

# Copy Python dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code from builder
COPY --from=builder --chown=pharma:pharma /app .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/backups /app/reports && \
    chown -R pharma:pharma /app && \
    chmod 755 /app/logs /app/data /app/backups /app/reports

# Add forensic metadata labels for GMP compliance
ARG BUILD_ID="unknown"
ARG GIT_COMMIT="unknown"
ARG BUILD_TIMESTAMP="unknown"
ARG BUILD_USER="system"

LABEL maintainer="Pharmaceutical Manufacturing Team" \
      application="pharma-manufacturing-monitoring" \
      version="1.0.0" \
      compliance="GMP/FDA" \
      build.id="${BUILD_ID}" \
      build.commit="${GIT_COMMIT}" \
      build.timestamp="${BUILD_TIMESTAMP}" \
      build.user="${BUILD_USER}" \
      security.scan="required" \
      regulatory.validation="required"

# Switch to non-root user
USER pharma

# Expose application port
EXPOSE 8000

# Health check for Kubernetes readiness/liveness probes
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

# Production command with gunicorn
CMD ["gunicorn", "src.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "60", "--keep-alive", "2"]

# =============================================================================
# Testing Stage - For running tests
# =============================================================================
FROM development as testing

# Install additional testing tools
RUN pip install coverage pytest-html pytest-xdist

# Copy test files
COPY tests/ tests/

# Set environment for testing
ENV TESTING=true
ENV DATABASE_URL=postgresql://test_user:test_pass@postgres:5432/test_pharma_db

# Test command
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=html", "--cov-report=term-missing"]

# =============================================================================
# Migrations Stage - For database migrations
# =============================================================================
FROM production as migrations

# Copy database migration scripts
COPY src/database/migrations/ src/database/migrations/
COPY scripts/migrate.py scripts/

# Migration command
CMD ["python", "scripts/migrate.py"]

# =============================================================================
# Reports Stage - For generating compliance reports
# =============================================================================
FROM production as reports

# Install additional reporting dependencies
USER root
RUN pip install weasyprint reportlab openpyxl
USER pharma

# Copy report templates
COPY templates/ templates/
COPY scripts/generate_reports.py scripts/

# Reports generation command
CMD ["python", "scripts/generate_reports.py"]

# =============================================================================
# Backup Stage - For data backup operations
# =============================================================================
FROM production as backup

# Install backup tools
USER root
RUN apt-get update && apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*
USER pharma

# Copy backup scripts
COPY scripts/backup.py scripts/
COPY scripts/restore.py scripts/

# Backup command
CMD ["python", "scripts/backup.py"]

# =============================================================================
# Security Scan Stage - For security validation
# =============================================================================
FROM production as security-scan

# Install security scanning tools
USER root
RUN pip install safety bandit semgrep
USER pharma

# Security scan command
CMD ["python", "-m", "safety", "check", "&&", "bandit", "-r", "src/", "&&", "semgrep", "--config=auto", "src/"]