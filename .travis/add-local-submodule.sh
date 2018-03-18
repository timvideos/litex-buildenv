#! /bin/bash

if [ "$(whoami)" == "root" ]
then
    echo "Please don't run this script as root!"
    exit 1
fi

SCRIPT_SRC=$(realpath ${BASH_SOURCE[0]})

set -e

#cd $SCRIPT_DIR/..

echo
USER_SLUG="$1"
SUBMODULE="$2"
REV=$(git rev-parse HEAD)

echo "Submodule $SUBMODULE"

# Get the pull request info
REQUEST_USER="$(echo $USER_SLUG | perl -pe 's|^([^/]*)/.*|\1|')"
REQUEST_REPO="$(echo $USER_SLUG | perl -pe 's|.*?/([^/]*)$|\1|')"

echo "Request user is '$REQUEST_USER'".
echo "Request repo is '$REQUEST_REPO'".

# Get current origin from git
ORIGIN_URL="$(git config -f .gitmodules submodule.$SUBMODULE.url)"
#ORIGIN_URL="$(git remote get-url origin)"
if echo $ORIGIN_URL | grep -q "github.com"; then
	echo "Found github"
else
	echo "Did not find github, skipping"
	exit 0
fi

ORIGIN_SLUG=$(echo $ORIGIN_URL | perl -pe 's|.*github.com/(.*?)(.git)?$|\1|')
echo "Origin slug is '$ORIGIN_SLUG'"

ORIGIN_USER="$(echo $ORIGIN_SLUG | perl -pe 's|^([^/]*)/.*|\1|')"
ORIGIN_REPO="$(echo $ORIGIN_SLUG | perl -pe 's|.*?/([^/]*)$|\1|')"

echo "Origin user is '$ORIGIN_USER'"
echo "Origin repo is '$ORIGIN_REPO'"

USER_URL="git://github.com/$REQUEST_USER/$ORIGIN_REPO.git"

# Check if the user's repo exists
echo -n "User's repo would be '$USER_URL' "
if git ls-remote --exit-code --heads "$USER_URL" > /dev/null 2>&1; then
	echo "which exists!"
else
	echo "which does *not* exist!"
	USER_URL="$ORIGIN_URL"
fi

# If submodule doesn't exist, clone directly from the users repo
if [ ! -e $SUBMODULE/.git ]; then
	echo "Cloning '$ORIGIN_REPO' from repo '$USER_URL'"
	git clone $USER_URL $SUBMODULE --origin user
fi
# If the submodule does exist, add a new remote.
(
	cd $SUBMODULE

	git remote rm user >/dev/null 2>&1 || true
	if [ "$USER_URL" != "$ORIGIN_URL" ]; then
		git remote add user $USER_URL
		git fetch user
	fi

	git remote rm origin >/dev/null 2>&1 || true
	git remote add origin $ORIGIN_URL
	git fetch origin
)

# Checkout the submodule at the right revision
git submodule update --init $SUBMODULE

# Call ourselves recursively.
(
	cd $SUBMODULE
	git submodule status
	echo
	git submodule status | while read SHA1 MODULE_PATH DESC
	do
		"$SCRIPT_SRC" "$USER_SLUG" "$MODULE_PATH"
	done
	exit 0
) || exit 1

exit 0
