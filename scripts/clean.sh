#!/bin/bash

set -e

# find all cache files and remove them
find . -name "__pycache__" | xargs rm -rf

# find coverage files and remove them
find . -name ".coverage" | xargs rm -rf
find . -name "*,cover" | xargs rm -rf
find . -name "htmlcov" | xargs rm -rf

# clean up pipenv packages
pipenv clean

echo "
Cleaned up the project!"
