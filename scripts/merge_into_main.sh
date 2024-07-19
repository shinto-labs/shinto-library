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
    exit_with_error "You must be on the development branch to merge into main."
fi

echo -e "${yellow}Warning${reset}: Make sure you pushed the latest changes to the development branch."

## Get the version number from setup.py
version_number=$(grep 'version=' setup.py | sed "s/.*version=['\"]\\([^'\"]*\\)['\"],/\\1/")

if [ -z "$version_number" ]; then
    exit_with_error "Version number could not be extracted from setup.py"
fi

## Get latest changes from development
echo "Getting latest development changes..."
git checkout development && git pull

## Get all tags from the remote repo
echo "Fetching all tags from GitHub."
git fetch --tag >/dev/null 2>&1

tags=($(git tag -l | tr '\n' ' '))
list_length=${#tags[@]}
last_tag=${tags[-1]}

if [ "$list_length" -eq 0 ]; then
    echo -e "${yellow}No tags found on the remote repo.${reset}"
else
    echo "Last deployed version: $last_tag."
fi

## Check if the version number in setup.py matches any tag
for tag in "${tags[@]}"; do
    if [[ "$tag" == "$version_number" ]]; then
        matching_tag=$tag
        break
    fi
done

if [ "$matching_tag" ]; then
    echo -e "${green}Info${reset}: Version number in setup.py matches tag: $matching_tag."

    ## Get the version number to deploy from the user
    echo "Proceeding will update the version in setup.py to your provided version and push to development."
    echo -n "What version do you want to deploy with? "
    read -r version
    regex="^[0-9]+\.[0-9]+\.[0-9]+$"
    if [[ -z "$version" ]]; then
        exit_with_error "Version cannot be empty."
    elif [[ "$tags" == *"$version"* ]]; then
        exit_with_error "Version matches existing tag: $tag."
    elif [[ ! "$version" =~ $regex ]]; then
        exit_with_error "Invalid version number. Version number must be in the format X.Y.Z."
    fi

    echo "Updating version in setup.py to $version and pushing to development."
    sed -i "s/version=['\"]\([^'\"]*\)['\"],/version=\"$version\",/" setup.py
    git add setup.py
    git commit -m "Update version in setup.py to $version"
    git push origin development
else
    if [ -z "$last_tag" ]; then
        echo "No tags found on the remote repo, creating first release."
    else
        echo -e "${red}Warning${reset}: Version number in setup.py does not match any tag."
    fi

    ## Confirm with the user to proceed with the version number in setup.py
    echo -n "Do you want to proceed with the version number \"version_number\" in setup.py? (y/n) "
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
git merge development --commit --no-ff -m "Merge into main version: $version" && git push main
