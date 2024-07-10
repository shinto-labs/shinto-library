#!/bin/bash

set -e

cd ../

VERSION_NUMBER=$(grep 'version=' setup.py | sed "s/.*version=['\"]\\([^'\"]*\\)['\"],/\\1/")

if [ -z "$VERSION_NUMBER" ]; then
    echo "Version number could not be extracted from setup.py"
    exit 1
fi

echo "Fetching latest tags from GitHub."
git tag -l | xargs git tag -d >/dev/null 2>&1
git fetch --tag >/dev/null 2>&1

set +e
LAST_TAG=$(git describe --tags $(git rev-list --tags --max-count=1) 2>/dev/null)
set -e

if [ -z "$LAST_TAG" ]; then
    echo "No tags found on the remote repo."
else
    echo "Last deployed version: $LAST_TAG"
fi

echo "What tag do you want to deploy with?"
read TAG
echo

if [ -z "$TAG" ]; then
    echo "No version number provided. Exiting."
    exit 1
fi

read -p "!! Make sure you pushed the latest changes to the development branch.
Are you sure you want merge development into main and create tag: $TAG? (y/n) " -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Exiting without merging and tagging."
    exit 1
fi

if [ "$VERSION_NUMBER" != "$TAG" ]; then
    read -p "Version number in setup.py does not match the tag.
Do you want to update the version in setup.py to $TAG and push to development? (y/n) " -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting without merging and tagging."
        exit 1
    fi

    echo "Updating version in setup.py to $TAG and pushing to development."
    sed -i "s/version=['\"]\([^'\"]*\)['\"],/version=\"$TAG\",/" setup.py
    git add setup.py
    git commit -m "Update version to $TAG"
    git push origin development
fi

echo "Get latest development changes and change branch to main."
git checkout development && git pull && git checkout main && git pull

echo "Merging development into main and tagging the version."
git merge development --commit --no-ff -m "Merge into main Version: $TAG" && git tag $TAG

echo "Pushing changes to main branch and tags."
git push origin main $TAG
