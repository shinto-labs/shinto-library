#!/bin/bash

set -e

# Refresh lock file
pdm lock --refresh

# Update dependencies
pdm update

echo "
🎉 Updated the dependencies!"
