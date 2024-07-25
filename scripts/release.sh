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
error_msg="There are uncommitted changes in the repository.
Please commit or stash the changes before deploying a new version."
if [ -n "$(git status --porcelain)" ]; then
    exit_with_error error_msg
fi

## Get the version number from pdm show
version_number=$(pdm show | grep 'Latest version:' | sed 's/Latest version:[[:space:]]*//')

if [ -z "$version_number" ]; then
    exit_with_error "Version number could not be extracted from pdm show"
fi

## Get latest changes from development
echo "Getting latest development changes..."
git checkout development && git pull

## Get all tags from the remote repo
echo "Fetching tags from GitHub."
git fetch --tag >/dev/null 2>&1

tags=($(git tag -l | tr '\n' ' '))
list_length=${#tags[@]}
last_tag=${tags[-1]}

if [ "$list_length" -eq 0 ]; then
    echo -e "${yellow}No tags found on the remote repo.${reset}"
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

## Prompt user with version number
if [ "$matching_tag" ]; then
    echo -e "${green}Info${reset}: Version number \"$version_number\" in pyproject.toml matches existing tag: $matching_tag."
    echo

    echo "In order to proceed with the release, we need to update the version number in pyproject.toml."
    echo -n "What version do you want to deploy with? "
    read -r new_version
    regex="^[0-9]+\.[0-9]+\.[0-9]+$"
    if [[ -z "$new_version" ]]; then
        exit_with_error "Version cannot be empty."
    elif [[ "$tags" == *"$new_version"* ]]; then
        exit_with_error "Version matches existing tag: $tag."
    elif [[ ! "$new_version" =~ $regex ]]; then
        exit_with_error "Invalid version number. Version number must be in the format X.Y.Z."
    fi

    echo "Updating version in pyproject.toml to $new_version and pushing to $current_branch."
    sed -i "s/version = ['\"]\([^'\"]*\)['\"],/version = \"$new_version\",/" pyproject.toml
    git add pyproject.toml
    git commit -m "Update version in pyproject.toml to $new_version"
    git push origin $current_branch

    version_number=$new_version
else
    if [ -z "$last_tag" ]; then
        echo "No tags found on the remote repo, creating first release."
    else
        echo -e "${red}Warning${reset}: Version number in pyproject.toml does not match any tag."
    fi

    ## Confirm with the user to proceed with the version number in pyproject.toml
    echo -n "Do you want to proceed with the version number \"$version_number\" in pyproject.toml? (y/n) "
    read -r response
    if [[ "$response" != "y" ]]; then
        exit_with_error "Exiting..."
    fi
fi

## Change branch to main
echo "Changing branch to main..."
git checkout main && git pull

## Merge development into main and push changes
echo "Merging development into main and tagging the version."
git merge development --commit --no-ff -m "Merge into main version: $version_number" && git push main
