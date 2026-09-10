# base stage
# ===========================
FROM python:3.14-slim AS base

LABEL maintainer="Aron Hemmes<aron@shintolabs.nl"
LABEL url="shintolabs.nl"
ARG BUILD_DATE
LABEL build-date=$BUILD_DATE

# build stage
# ==================
FROM base AS builder

## install git
RUN apt update && apt install -y git curl build-essential

## install safe chain
RUN curl -fsSL https://github.com/AikidoSec/safe-chain/releases/latest/download/install-safe-chain.sh | sh -s -- --ci && \
    export PATH="/root/.safe-chain/shims:/root/.safe-chain/bin:${PATH}" && \
    pip safe-chain-verify
ENV PATH="/root/.safe-chain/shims:/root/.safe-chain/bin:${PATH}"
ENV SAFE_CHAIN_LOGGING=verbose

## install pdm
RUN pip install pdm && \
    pdm safe-chain-verify

## install shinto-library as a package, plus integration-test dependencies
COPY pyproject.toml README.md /library/
COPY shinto /library/shinto/
COPY integration_tests/pyproject.toml ./pyproject.toml
RUN pdm lock && pdm sync --no-editable


# Runtime stage
# ==================
FROM base AS runtime

WORKDIR /integration_tests

ENV PATH="/.venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /.venv /.venv
COPY integration_tests/ /integration_tests/

CMD [ "python", "-u", "/integration_tests/main.py" ]
