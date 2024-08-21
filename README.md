# Shinto Library

Library of shared Python modules for use in Shinto projects.

## Installation and standard usage of library

To install the library run:
`pdm add git+ssh://git@github.com/shinto-labs/shinto-library.git@<release>`

or with pip:
`pip install git+ssh://git@github.com/shinto-labs/shinto-library.git@<release>`

To use the library simply use:

```
import shinto
# or a specific method
from shinto import <package>
```

## Prerequisites

- **python**
- **make**
- **git**

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

# Git

C:\Program Files\Git\bin
C:\Program Files\Git\cmd
```

</details>

## Development Actions

Refer to the [Makefile](./Makefile) for a full list of commands.

### Install

Run: `make install`

And follow the instructions in the output.

### Update

Run: `make update`

Updates packages and synchronises the [pdm.lock](./pdm.lock) file with the packages in [pyproject.toml](./pyproject.toml).

### Release / Deployment

Create a release by running: `make release`

This merges development into main and creates a release with the provided tag.

### Testing

Execute unit tests: `make test`

For coverage: `make test_coverage`

Format check: `make ruff`

### Clean up the development environment

Clean caches and environments with: `make clean`

This cleans caches and environments.
