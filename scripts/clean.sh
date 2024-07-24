#!/bin/bash

set -e

# find all cache files and remove them
find . -name "__pycache__" | xargs rm -rf

# find build files and remove them
find . -name "build" | xargs rm -rf

# find coverage files and remove them
find . -name ".coverage" | xargs rm -rf
find . -name "*,cover" | xargs rm -rf
find . -name "htmlcov" | xargs rm -rf

# clean up pipenv packages
pipenv clean

# if --hard flag is passed, reset environment
if [[ " $* " == *" --hard "* ]]; then
    # remove virtual environment
    venv_path=$(pipenv --venv)
    rm -rf $venv_path

    # find egg-info files and remove them
    find . -name "*.egg-info" | xargs rm -rf
fi

echo "Cleaned up the project!"
