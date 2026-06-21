# Stage 1: Builder — MUST match runtime base for native extensions
# Alpine uses musl libc. If the runtime is switched to slim, switch
# builder here too and use: python:3.13-slim with gcc + libpython-dev.
FROM python:3.13-alpine AS builder

# Install uv and build dependencies
# - libstdc++: required by matplotlib
# - gcc, python-dev, make: for compiling psutil, pydantic-core extensions
RUN apk add --no-cache \
        curl \
        libstdc++ \
        gcc \
        g++ \
        make \
        linux-headers \
        python3-dev \
        musl-dev

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Pre-install dependencies into a virtual environment
RUN uv sync --frozen --no-install-project --no-dev

# Copy source and install the project
COPY . .
RUN uv sync --frozen --no-dev

# Stage 2: Runtime (minimal Alpine)
# NOTE: Alpine uses musl libc instead of glibc. If there are C extension
# runtime errors (pyproj), switch the base image to python:3.13-slim
FROM python:3.13-alpine AS runtime

# Install runtime dependencies only
# - ca-certificates: for HTTPS outgoing connections
# - libproj (runtime linker): required by pyproj
RUN apk add --no-cache \
    ca-certificates \
    proj-util \
    libstdc++

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY --from=builder /app/main.py .
COPY --from=builder /app/settings.py .
COPY --from=builder /app/models ./models
COPY --from=builder /app/interfaces ./interfaces
COPY --from=builder /app/devices ./devices
COPY --from=builder /app/storage ./storage
COPY --from=builder /app/strategies ./strategies
COPY --from=builder /app/utils ./utils

CMD ["python", "main.py"]
