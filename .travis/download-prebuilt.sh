#!/bin/bash

# Clone prebuilt repo to copy results into
if [ ! -z "$TRAVIS_PULL_REQUEST" -a "$TRAVIS_PULL_REQUEST" != "false" ]; then
	# Don't do prebuilt for a pull request.
	echo ""
	echo ""
	echo ""
	echo "- Pull request, so no prebuilt pushing."
elif [ -z "$GH_TOKEN" ]; then
	# Only if run by travis display error
	if [ ! -z $TRAVIS_BUILD_NUMBER  ]; then
		echo ""
		echo ""
		echo ""
		echo "- No Github token so unable to copy built files"
	fi
elif [ -z "$TRAVIS_BRANCH" ]; then
	echo ""
	echo ""
	echo ""
	echo "- No branch name, unable to copy built files"
elif [ ! -z "$PREBUILT_DIR" ]; then
	# Look at repo we are running in to determine where to try pushing to if in a fork
	PREBUILT_REPO=HDMI2USB-firmware-prebuilt
	PREBUILT_REPO_OWNER=$(echo $TRAVIS_REPO_SLUG|awk -F'/' '{print $1}')
	echo ""
	echo ""
	echo ""
	echo "- Download built files from github.com/$PREBUILT_REPO_OWNER/$PREBUILT_REPO (to upload results)"
	echo "---------------------------------------------"
	(
		# Do a sparse, shallow checkout to keep disk space usage down.
		mkdir -p $PREBUILT_DIR
		cd $PREBUILT_DIR
		git init > /dev/null
		git config core.sparseCheckout true
		(
			git remote add origin https://$GH_TOKEN@github.com/$PREBUILT_REPO_OWNER/${PREBUILT_REPO}.git
		) > /dev/null
		cat > .git/info/sparse-checkout <<EOF
*.md
archive/*
archive/*/*
!archive/*/*/*
archive/**/sha256sum.txt
**/stable
**/testing
**/unstable
EOF
		git fetch -v --depth 1 origin master
		git checkout master
		echo ""
		PREBUILT_DIR_DU=$(du -h -s . | sed -e's/[ \t]*\.$//')
		echo "Prebuilt repo checkout is using $PREBUILT_DIR_DU"
		ls -l $PWD
		ls -l $PREBUILT_DIR
	)
	echo "============================================="
else
	echo ""
	echo ""
	echo ""
	echo "- No PREBUILD_DIR value found."
fi
