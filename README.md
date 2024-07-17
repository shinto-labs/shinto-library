# Shinto Library

Library of shared Python modules for use in Shinto projects.

## Prerequisites

- **python**
- **make**
- **psql**
- **git**
- **pipenv**

<details>
<summary>For Windows users</summary>

Make sure the commandline tools are added to your system's environment variables `PATH`.

Required paths (might be different depending on your installation/location):

```markdown
# Python

%USERPROFILE%\AppData\Local\Programs\Python\Python312
%USERPROFILE%\AppData\Local\Programs\Python\Python312\Scripts

# Make

C:\Program Files (x86)\GnuWin32\bin

# psql

C:\Program Files\PostgreSQL\16\bin

# Git

C:\Program Files\Git\bin
C:\Program Files\Git\cmd
```

</details>

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
