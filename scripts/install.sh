#!/bin/bash

set -e

pip install pipenv

pipenv install --dev

current_folder_name=$(basename "$(pwd)")

echo "Installation complete."
echo "In Visual Studio Code, set the venv as your Python interpreter:"
echo "1. Open the Command Palette (Ctrl+Shift+P)"
echo "2. Type 'Python: Select Interpreter'"
echo "3. Select the venv (e.g. ~\\.virtualenvs\\$current_folder_name-[ID]\\Scripts\\python.exe)"
