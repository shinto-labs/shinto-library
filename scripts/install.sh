#!/bin/bash

set -e

green='\033[0;32m'
reset='\033[0m'

# Install dependencies
pdm install

# Activate the virtual environment
source ./.venv/Scripts/activate

# Provide instructions for the user
echo -e "In Visual Studio Code, set the venv as your Python interpreter:
1. Open the Command Palette ${green}Ctrl+Shift+P${reset}
2. Type ${green}Python: Select Interpreter${reset}
3. Select the venv: ${green}.\\.venv\\Scripts\\python.exe${reset}
"
