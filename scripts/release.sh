#!/bin/bash

# This script is used to deploy a new version of the project.
# It merges the development branch into main and tags the version.
# It also updates the version number in pyproject.toml if necessary.

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

## Check for uncommitted changes or commited but unpushed changes
if [ -n "$(git status --porcelain)" ] || ! git status | grep -q "Your branch is up to date with"; then
    exit_with_error "There are uncommitted changes in the repository.
Please commit or stash the changes before deploying a new version."
fi

## Get the version number from pyproject.toml
version_number=$(grep 'version =' pyproject.toml | sed -E "s/.*version[[:space:]]*=[[:space:]]*['\"]([^'\"]*)['\"].*/\1/")

if [ -z "$version_number" ]; then
    exit_with_error "Version number could not be extracted from pdm show"
fi

## Get latest changes from development
echo "Getting latest development changes..."
git checkout development && git pull

## Get all tags from the remote repo
echo "Fetching tags from GitHub."
git tag -l | xargs git tag -d >/dev/null 2>&1
git fetch --tag >/dev/null 2>&1

tags=($(git tag -l --sort=-creatordate | tr '\n' ' '))
list_length=${#tags[@]}
last_tag=${tags[0]}

if [ "$list_length" -eq 0 ]; then
    echo -e "${yellow}No tags found on the remote repo, creating first release.${reset}"
else
    echo "Last released tag: $last_tag."
fi

## Check if the version number matches any tag
for tag in "${tags[@]}"; do
    if [[ "$tag" == "v$version_number" ]]; then
        matching_tag=$tag
        break
    fi
done

## Check if the version number in pyproject.toml matches any tag, if not, ask the user to proceed
if [ "$matching_tag" ]; then
    echo -e "${green}Info${reset}: Version number \"$version_number\" in pyproject.toml matches existing tag: $matching_tag."
    echo
    echo "In order to proceed with the release, we need to update the version number in pyproject.toml."
else
    if [ "$last_tag" ]; then
        echo -e "${red}Warning${reset}: Version number in pyproject.toml does not match any existing tags."
    fi

    ## Confirm with the user to proceed with the version number in pyproject.toml
    echo -n "Do you want to create release \"v$version_number\"? (y/n) "
    read -r response
fi

## If the user does not want to proceed with the version number in pyproject.toml, ask for a new version number
if [ "$matching_tag" ] || [ "$response" != "y" ]; then
    echo -n "What version do you want to deploy with? (eg 1.2.3) "
    read -r new_version
    regex="^v?[0-9]+\.[0-9]+\.[0-9]+$"
    if [[ -z "$new_version" ]]; then
        exit_with_error "Version cannot be empty."
    elif [[ "$tags" == *"$new_version"* ]]; then
        exit_with_error "Version matches existing tag: $matching_tag."
    elif [[ ! "$new_version" =~ $regex ]]; then
        exit_with_error "Invalid version number. Version number must be in the format 1.2.3 or v1.2.3."
    fi
    new_version=${new_version#v}

    echo "Updating version in pyproject.toml to $new_version and pushing to $current_branch."
    sed -i "s/version = ['\"]\([^'\"]*\)['\"]/version = \"$new_version\"/" pyproject.toml
    git add pyproject.toml
    git commit -m "Update version in pyproject.toml to $new_version"
    git push origin $current_branch

    version_number=$new_version
fi

echo "VERSION_NUMBER: $version_number"
tag="v$version_number"

## Change branch to main
echo "Changing branch to main..."
git checkout main && git pull

## Merge development into main
echo "Merging development into main."
git merge development --commit --no-ff -m "Merge into main version: $tag"

## Create tag and push to main
echo "Creating tag $tag and pushing to main."
git tag $tag && git push origin main $tag

echo "
🎉 Created release $tag!"
