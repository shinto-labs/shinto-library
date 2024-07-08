#!/bin/bash

set -e

VERSION_NUMBER=$(grep 'version=' setup.py | sed "s/.*version=['\"]\\([^'\"]*\\)['\"],/\\1/")

if [ -z "$VERSION_NUMBER" ]; then
    echo "Version number could not be extracted from setup.py"
    exit 1
fi

read -p """Make sure you pushed the latest changes to the development branch.
Are you sure you want merge development into main and create a tag with version $VERSION_NUMBER? (y/n)""" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Exiting without merging and tagging."
    exit 1
fi

echo "Get latest development changes and change branch to main."
git checkout development && git pull && git checkout main && git pull

echo "Merging development into main and tagging the version."
git merge development --commit --no-ff -m "Merge into main Version: $VERSION_NUMBER" && git tag $VERSION_NUMBER

echo "Pushing changes to main branch and tags."
git push origin main $VERSION_NUMBER
