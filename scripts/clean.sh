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

# find ruff cache files and remove them
find . -name ".ruff_cache" | xargs rm -rf

# find egg files and remove them
find . -name "*.egg-info" | xargs rm -rf

# find venv files and remove them
find . -name ".venv" | xargs rm -rf
find . -name ".pdm-python" | xargs rm -rf

echo "
🎉 Cleaned up the project!"
