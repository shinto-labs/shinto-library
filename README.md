# Shinto Library

Library for shared config and connections for Shinto repositories

## Prerequisites

- make
- python
- git

#### Aditional Windows prerequisites:

- Git Bash (make sure installation path is added to env variables e.g. C:\Program Files\Git\bin)

## Actions

Full list of commands in: [Makefile](./Makefile)

Make sure to install the dependencies with `make install`

### Release / Deployment

Run `make release`

This merges development into main and creates a release with the provided tag.

### Testing

#### Run unit tests: `make test`

#### Run unit tests with coverage: `make test_coverage`

#### Check ruff format: `make ruff`
