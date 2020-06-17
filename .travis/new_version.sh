#!/bin/bash

if [ "$TRAVIS_BRANCH" == "master" ]; then 
     export VERSION=$(cat VERSION.txt);
     NEW_VERSION=$(echo "$VERSION + 0.1" | bc)
     echo $NEW_VERSION > VERSION.txt
	 
	 ## update develop branch also ##
	 git fetch	 
	 git checkout develop
     git add VERSION.txt
	 git commit -m "Updating version.txt"
	 git push origin HEAD:develop
else
     echo "Skipping new version tag because current branch is not master";
fi
