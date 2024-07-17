#!/bin/bash

set -e

yellow='\033[1;93m'
green='\033[0;32m'
reset='\033[0m'

pipenv install --dev

venv_path=$(pipenv --venv)

echo -e "

===================================================

Installation complete.

In Visual Studio Code, set the venv as your Python interpreter:
1. Open the Command Palette ${green}Ctrl+Shift+P${reset}
2. Type ${green}Python: Select Interpreter${reset}
3. Select the venv: ${green}${venv_path}\\Scripts\\python.exe${reset}"

# Shell cannot be activated from a bash script, so we can only provide instructions
if [ -z "$PIPENV_ACTIVE" ]; then
    echo -e "
To activate this project's virtualenv in shell, run: ${yellow}pipenv shell${reset}
Alternatively, run a command inside the virtualenv with ${yellow}pipenv run <command>${reset}
"
else
    echo -e "
${green}Virtualenv is already activated in shell.${reset}
"
fi
