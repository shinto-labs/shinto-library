#!/bin/bash

set -e

yellow='\033[0;33m'
green='\033[0;32m'
reset='\033[0m'

# Get os type
os_is_windows=false
if [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then
    os_is_windows=true
fi

# Install pdm if not already installed
if ! command -v pdm &>/dev/null; then
    echo -e "${yellow}pdm is not installed. Installing...${reset}"
    if $os_is_windows; then
        python -m pip install pdm
    else
        sudo apt install python3-venv
        curl -sSL https://pdm-project.org/install-pdm.py | python3
    fi
fi

# Install dependencies
pdm install

# Provide instructions for the user
activate_script_location=".venv/bin/activate"
if $os_is_windows; then
    activate_script_location=".venv/Scripts/activate"
fi
echo -e "🎉 Installed the dependencies!

To activate this project's virtualenv, run ${yellow}source $activate_script_location${reset}
Alternatively, run a command inside the virtualenv with ${yellow}pdm run <command>${reset}

In Visual Studio Code, set the venv as your Python interpreter:
1. Open the Command Palette ${green}Ctrl+Shift+P${reset}
2. Type ${green}Python: Select Interpreter${reset}
3. Select the venv: ${green}.\\.venv\\Scripts\\python.exe${reset}"
