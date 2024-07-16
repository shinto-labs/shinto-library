#!/bin/bash

set -e

if [[ "$VIRTUAL_ENV" == "" ]]; then
    pip install pipenv >/dev/null
fi

pipenv install --dev >/dev/null

current_folder_name=$(basename "$(pwd)")

echo "Installation complete."
echo
echo "In Visual Studio Code, set the venv as your Python interpreter:"
echo -e "1. Open the Command Palette \e[93mCtrl+Shift+P\e[0m"
echo -e "2. Type \e[93mPython: Select Interpreter\e[0m"
echo -e "3. Select the venv: \e[93m~\\.virtualenvs\\$current_folder_name-[ID]\\Scripts\\python.exe\e[0m"
echo
echo -e "To activate this project's virtualenv in shell, run: \e[93mpipenv shell\e[0m"
