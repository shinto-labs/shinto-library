#!/bin/bash

set -e

red='\033[0;31m'
yellow='\033[1;93m'
green='\033[0;32m'
reset='\033[0m'

exit_with_error() {
    local message=$1
    echo -e "${red}${message}${reset}"
    exit 1
}

if [ "$(git rev-parse --abbrev-ref HEAD)" != "development" ]; then
    exit_with_error "You must be on the development branch to deploy a new version."
fi

echo -e "${yellow}Warning${reset}: Make sure you pushed the latest changes to the development branch."

VERSION_NUMBER=$(grep 'version=' setup.py | sed "s/.*version=['\"]\\([^'\"]*\\)['\"],/\\1/")

if [ -z "$VERSION_NUMBER" ]; then
    exit_with_error "Version number could not be extracted from setup.py"
fi

echo "Fetching latest tags from GitHub."
git tag -l | xargs git tag -d >/dev/null 2>&1
git fetch --tag >/dev/null 2>&1

set +e
LAST_TAG=$(git describe --tags $(git rev-list --tags --max-count=1) 2>/dev/null)
set -e

if [ -z "$LAST_TAG" ]; then
    echo -e "${yellow}No tags found on the remote repo.${reset}"
else
    echo "Last deployed version: $LAST_TAG"
fi

echo -n "What tag do you want to deploy with? "
read -r TAG

if [ -z "$TAG" ]; then
    exit_with_error "Tag cannot be empty."
fi

echo -n "Are you sure you want merge development into main and create tag: $TAG? (y/n) "
read -r REPLY
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit_with_error "Exiting."
fi

if [ "$VERSION_NUMBER" != "$TAG" ]; then
    echo -e "${green}Version number in setup.py does not match the tag.${reset}"
    echo -n "Do you want to update the version in setup.py to $TAG and push to development? (y/n) "
    read -r REPLY
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit_with_error "Exiting."
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
