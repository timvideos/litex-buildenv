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

echo "Submodule $SUBMODULE @ $REV"

# Get the pull request info
REQUEST_USER="$(echo $USER_SLUG | perl -pe 's|^([^/]*)/.*|\1|')"
REQUEST_REPO="$(echo $USER_SLUG | perl -pe 's|.*?/([^/]*)$|\1|')"

echo "Request user is '$REQUEST_USER'".
echo "Request repo is '$REQUEST_REPO'".

# Get current origin from git
ORIGIN="$(git config -f .gitmodules submodule.$SUBMODULE.url)"
#ORIGIN="$(git remote get-url origin)"
if echo $ORIGIN | grep -q "github.com"; then
	echo "Found github"
else
	echo "Did not find github, skipping"
	exit 0
fi

ORIGIN_SLUG=$(echo $ORIGIN | perl -pe 's|.*github.com/(.*?)(.git)?$|\1|')
echo "Origin slug is '$ORIGIN_SLUG'"

ORIGIN_USER="$(echo $ORIGIN_SLUG | perl -pe 's|^([^/]*)/.*|\1|')"
ORIGIN_REPO="$(echo $ORIGIN_SLUG | perl -pe 's|.*?/([^/]*)$|\1|')"

echo "Origin user is '$ORIGIN_USER'"
echo "Origin repo is '$ORIGIN_REPO'"

USER_URL="git://github.com/$REQUEST_USER/$ORIGIN_REPO.git"

echo "Users repo would be '$USER_URL'"

if [ ! -e $SUBMODULE/.git ]; then
	echo "Successfully cloned from user repo '$USER_URL'"
	$(which git) clone $USER_URL $SUBMODULE --origin user || true
	if [ -d $SUBMODULE/.git ]; then
		echo "Successfully cloned from user repo '$ORIGIN_REPO'"
	fi
fi
if [ -e $SUBMODULE/.git ]; then
	(
		cd $SUBMODULE
		git remote add user $USER_URL || git remote set-url user $USER_URL
		$(which git) fetch user || git remote rm user

		git remote add origin $ORIGIN || git remote set-url origin $ORIGIN
		$(which git) fetch origin
	)
fi

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
