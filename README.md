# Shinto Library

Library for shared modules in Shinto repositories

## Prerequisites

#### Commandline tools

- **python**
- **make**
- **psql**
- **git**

For windows users make sure the tools are added to your system's environment variables `PATH`.

#### Setup Virtual Environment

```
python -m venv dev-env
source dev-env/bin/activate
```

## Development Actions

Refer to the [Makefile](./Makefile) for a full list of commands.

### Install

Install dependencies with: `make install`

### Release / Deployment

Create a release by running: `make release`

This merges development into main and creates a release with the provided tag.

### Testing

Execute unit tests: `make test`

For coverage: `make test_coverage`

Format check: `make ruff`

### Clean up the development environment

Clean caches and environments with: `make clean`
