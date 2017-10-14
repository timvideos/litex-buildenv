#!/bin/bash

set -e

echo ""
echo ""
echo ""
echo "- Fetching non shallow to get git version"
echo "---------------------------------------------"
git fetch origin --unshallow && git fetch origin --tags

if [ z"$TRAVIS_PULL_REQUEST_SLUG" != z ]; then
	echo ""
	echo ""
	echo ""
	echo "- Fetching from pull request source"
	echo "---------------------------------------------"
	git remote add source https://github.com/$TRAVIS_PULL_REQUEST_SLUG.git
	git fetch source --unshallow && git fetch source --tags

	echo ""
	echo ""
	echo ""
	echo "- Fetching from pull request source"
	echo "---------------------------------------------"
	git fetch origin pull/$TRAVIS_PULL_REQUEST/head:pull-$TRAVIS_PULL_REQUEST-head
	echo "---------------------------------------------"
	git log -n 5 --graph pull-$TRAVIS_PULL_REQUEST-head
	echo "---------------------------------------------"
fi

if [ z"$TRAVIS_BRANCH" != z ]; then
	TRAVIS_COMMIT_ACTUAL=$(git log --pretty=format:'%H' -n 1)
	echo ""
	echo ""
	echo ""
	echo "Fixing detached head (current $TRAVIS_COMMIT_ACTUAL -> $TRAVIS_COMMIT)"
	echo "---------------------------------------------"
	git log -n 5 --graph
	echo "---------------------------------------------"
	git fetch origin $TRAVIS_COMMIT
	git branch -v
	echo "---------------------------------------------"
	git log -n 5 --graph
	echo "---------------------------------------------"
	git branch -D $TRAVIS_BRANCH || true
	git checkout $TRAVIS_COMMIT -b $TRAVIS_BRANCH
	git branch -v
fi
echo ""
echo ""
echo ""
echo "Git Revision"
echo "---------------------------------------------"
git status
echo "---------------------------------------------"
git describe
echo "============================================="
GIT_REVISION=$(git describe)

set -x

# Run the script once to check it works
time scripts/download-env.sh
# Run the script again to check it doesn't break things
time scripts/download-env.sh

set +x
set +e
source scripts/enter-env.sh
