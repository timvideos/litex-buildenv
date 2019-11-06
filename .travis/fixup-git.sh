#!/bin/bash

set -e

# Disable prompting for passwords - works with git version 2.3 or above
export GIT_TERMINAL_PROMPT=0
# Harder core version of disabling the username/password prompt.
GIT_CREDENTIAL_HELPER=$PWD/.git/git-credential-stop
cat > $GIT_CREDENTIAL_HELPER <<EOF
cat
echo "username=git"
echo "password=git"
EOF
chmod a+x $GIT_CREDENTIAL_HELPER
git config credential.helper $GIT_CREDENTIAL_HELPER

# Create a global .gitignore and populate with Python stuff
GIT_GLOBAL_IGNORE=$PWD/.git/ignore
cat > $GIT_GLOBAL_IGNORE <<EOF
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
EOF
git config --global core.excludesfile $GIT_GLOBAL_IGNORE

DF_BEFORE_GIT="$(($(stat -f --format="%a*%S" .)))"

echo ""
echo ""
echo ""
echo "- Fetching non shallow to get git version"
echo "---------------------------------------------"
if git rev-parse --is-shallow-repository; then
	git fetch origin --unshallow
fi
git fetch origin --tags

TRAVIS_COMMIT_ACTUAL=$(git log --pretty=format:'%H' -n 1)

if [ z"$TRAVIS_PULL_REQUEST_SLUG" != z ]; then
	echo ""
	echo ""
	echo ""
	echo "- Fetching from pull request source"
	echo "---------------------------------------------"
	git remote add source https://github.com/$TRAVIS_PULL_REQUEST_SLUG.git
	git fetch source && git fetch --tags

	echo ""
	echo ""
	echo ""
	echo "- Fetching the actual pull request"
	echo "---------------------------------------------"
	git fetch origin pull/$TRAVIS_PULL_REQUEST/head:pull-$TRAVIS_PULL_REQUEST-head
	git fetch origin pull/$TRAVIS_PULL_REQUEST/merge:pull-$TRAVIS_PULL_REQUEST-merge
	echo "---------------------------------------------"
	git log -n 5 --graph pull-$TRAVIS_PULL_REQUEST-head
	echo "---------------------------------------------"
	git log -n 5 --graph pull-$TRAVIS_PULL_REQUEST-merge
	echo "---------------------------------------------"

	GITHUB_CURRENT_MERGE_SHA1="$(git log --pretty=format:'%H' -n 1 pull-$TRAVIS_PULL_REQUEST-merge)"
	if [ "$GITHUB_CURRENT_MERGE_SHA1" != "$TRAVIS_COMMIT" ]; then
		echo ""
		echo ""
		echo ""
		echo "- Pull request triggered for $TRAVIS_COMMIT but now at $GITHUB_CURRENT_MERGE_SHA1"
		echo ""
	fi
	if [ "$GITHUB_CURRENT_MERGE_SHA1" != "$TRAVIS_COMMIT_ACTUAL" ]; then
		echo ""
		echo ""
		echo ""
		echo "- Pull request triggered for $TRAVIS_COMMIT_ACTUAL but now at $GITHUB_CURRENT_MERGE_SHA1"
		echo ""
	fi

	echo ""
	echo ""
	echo ""
	echo "- Using pull request version of submodules (if they exist)"
	echo "---------------------------------------------"
	$PWD/.travis/add-local-submodules.sh $TRAVIS_PULL_REQUEST_SLUG
	echo "---------------------------------------------"
	git submodule foreach --recursive 'git remote -v; echo'
	echo "---------------------------------------------"
fi

if [ z"$TRAVIS_REPO_SLUG" != z ]; then
	echo ""
	echo ""
	echo ""
	echo "- Using local version of submodules (if they exist)"
	echo "---------------------------------------------"
	$PWD/.travis/add-local-submodules.sh $TRAVIS_REPO_SLUG
	echo "---------------------------------------------"
	git submodule foreach --recursive 'git remote -v; echo'
	echo "---------------------------------------------"
fi

echo "---------------------------------------------"
git submodule status --recursive
echo "---------------------------------------------"

if [ "$TRAVIS_COMMIT_ACTUAL" != "$TRAVIS_COMMIT" ]; then
	echo ""
	echo ""
	echo ""
	echo "- Build request triggered for $TRAVIS_COMMIT but got $TRAVIS_COMMIT_ACTUAL"
	echo ""
	TRAVIS_COMMIT=$TRAVIS_COMMIT_ACTUAL
fi

if [ z"$TRAVIS_BRANCH" != z ]; then
	echo ""
	echo ""
	echo ""
	echo "Fixing detached head (current $TRAVIS_COMMIT_ACTUAL)"
	echo "---------------------------------------------"
	git log -n 5 --graph
	echo "---------------------------------------------"
	git branch -D $TRAVIS_BRANCH || true
	git checkout $TRAVIS_COMMIT_ACTUAL -b $TRAVIS_BRANCH
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

echo ""
echo ""
echo ""
echo "- Disk space free (after fixing git)"
echo "---------------------------------------------"
df -h
echo ""
DF_AFTER_GIT="$(($(stat -f --format="%a*%S" .)))"
awk "BEGIN {printf \"Git is using %.2f megabytes\n\",($DF_BEFORE_GIT-$DF_AFTER_GIT)/1024/1024}"
