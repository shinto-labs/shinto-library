#!/bin/bash

set -e

VERSION_NUMBER=$(grep 'version=' setup.py | sed "s/.*='\\(.*\\)',/\\1/")

if [ -z "$VERSION_NUMBER" ]; then
    echo "Version number could not be extracted from setup.py"
    exit 1
fi

echo "Get latest development changes and change branch to main."
git checkout development && git pull && git checkout main && git pull

echo "Merging development into main and tagging the version."
git merge development --commit --no-ff -m "Merge into main Version: $VERSION_NUMBER" && git tag $VERSION_NUMBER

echo "Pushing changes to main branch and tags."
git push origin main $VERSION_NUMBER

echo "Creating a release."
git release create "$VERSION_NUMBER" --title "Release $VERSION_NUMBER" --notes "Release $VERSION_NUMBER"
