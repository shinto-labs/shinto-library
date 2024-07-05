#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Version number is not set, usage: ./deploy.sh version_number"
    exit 1
fi
VERSION_NUMBER=$1

echo "Get latest development changes and change branch to main."
git checkout development && git pull && git checkout main && git pull

echo "Merging development into main and tagging the version."
git merge development --commit --no-ff -m "Merge into main Version: $VERSION_NUMBER" && git tag $VERSION_NUMBER

echo "Pushing changes to main branch and tags."
git push origin main $VERSION_NUMBER
