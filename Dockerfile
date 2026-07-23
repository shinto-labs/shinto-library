# Base stage
# ===========================
FROM python:3.14-slim as base

LABEL maintainer="Tommy van Schie <tommy@shintolabs.nl>"
LABEL url="shintolabs.nl"
ARG BUILD_DATE
LABEL build-date=$BUILD_DATE

# Build stage
# ==================
FROM base AS builder

WORKDIR /shinto

# Install system dependencies including git
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
copy shinto/ /shinto/
copy integration_tests/ /integration_tests/

## install safe chain
RUN curl -fsSL https://github.com/AikidoSec/safe-chain/releases/latest/download/install-safe-chain.sh | sh -s -- --ci && \
    export PATH="/root/.safe-chain/shims:/root/.safe-chain/bin:${PATH}" && \
    pip safe-chain-verify
ENV PATH="/root/.safe-chain/shims:/root/.safe-chain/bin:${PATH}"
ENV SAFE_CHAIN_LOGGING=verbose

# Install dependencies
RUN pip install --no-cache-dir -e /shinto

# Runtime stage
# ==================
FROM base AS runtime

WORKDIR /integration_tests
COPY integration_tests/ /integration_tests/

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*


# Copy application code
COPY pyproject.toml /pyproject.toml
COPY --from=builder /shinto/ /shinto/

CMD [ "python", "-u", "/integration_tests/main.py" ]
