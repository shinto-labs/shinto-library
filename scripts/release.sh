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

## Get the current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "development" ]; then
    exit_with_error "You must be on the development branch to deploy a new version."
fi

echo -e "${yellow}Warning${reset}: Make sure you pushed the latest changes to the development branch."

## Get the version number from setup.py
version_number=$(grep 'version=' setup.py | sed "s/.*version=['\"]\\([^'\"]*\\)['\"],/\\1/")

if [ -z "$version_number" ]; then
    exit_with_error "Version number could not be extracted from setup.py"
fi

## Get the latest tag from GitHub
echo "Fetching latest tags from GitHub."
git tag -l | xargs git tag -d >/dev/null 2>&1
git fetch --tag >/dev/null 2>&1

set +e
last_tag=$(git describe --tags $(git rev-list --tags --max-count=1) 2>/dev/null)
set -e

if [ -z "$last_tag" ]; then
    echo -e "${yellow}No tags found on the remote repo.${reset}"
else
    echo "Last deployed version: $last_tag"
fi

## Get the tag to release from the user
echo -n "What tag do you want to deploy with? "
read -r tag

if [ -z "$tag" ]; then
    exit_with_error "Tag cannot be empty."
fi

## Confirmation prompt the user
echo -n "Are you sure you want merge development into main and create tag: $tag? (y/n) "
read -r reply
if [[ ! $reply =~ ^[Yy]$ ]]; then
    exit_with_error "Exiting."
fi

## Check if the version number in setup.py matches the tag, if not update it
if [ "$version_number" != "$tag" ]; then
    echo -e "${yellow}Info${reset}: Version number in setup.py does not match the tag."
    echo -n "Do you want to update the version in setup.py to $tag and push to development? (y/n) "
    read -r reply
    if [[ ! $reply =~ ^[Yy]$ ]]; then
        exit_with_error "Exiting."
    fi

    echo "Updating version in setup.py to $tag and pushing to development."
    sed -i "s/version=['\"]\([^'\"]*\)['\"],/version=\"$tag\",/" setup.py
    git add setup.py
    git commit -m "Update version to $tag"
    git push origin development
fi

## Get latest changes from development and change branch to main
echo "Get latest development changes and change branch to main."
git checkout development && git pull && git checkout main && git pull

## Merge development into main and tag the version
echo "Merging development into main and tagging the version."
git merge development --commit --no-ff -m "Merge into main Version: $tag" && git tag $tag

## Push changes to main branch and release tag
echo "Pushing changes to main branch and release tag."
git push origin main $tag
