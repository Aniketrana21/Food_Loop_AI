# ==============================================================================
# FoodLoop AI - Enterprise Production Dockerfile (Backend API)
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools and libpq development headers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies in isolated wheel cache
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# Final Production Runtime Stage
# ==============================================================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime dependencies only (libpq5 for PostgreSQL and curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-privileged system user for enterprise security
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Copy application source code
COPY --chown=appuser:appgroup backend /app/backend
COPY --chown=appuser:appgroup ml /app/ml

# Set working directory to backend application
WORKDIR /app/backend

# Switch to non-root user
USER appuser

EXPOSE 8000

# Docker native health check using GET /health
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production server start: Uvicorn with production worker configuration
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
