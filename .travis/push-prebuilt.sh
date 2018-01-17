#!/bin/bash
exit 0
if [ -d "$PREBUILT_DIR" ]; then
	echo ""
	echo ""
	echo ""
	echo "Pushing prebuilt binaries"
	echo "============================================="
	(
	cd $PREBUILT_DIR
	for i in 1 2 3 4 5 6 7 8 9 10; do	# Try 10 times.
		if [ "$TRAVIS_BRANCH" = "master" ]; then
			echo "Pushing with PLATFORMS='$PLATFORMS'"
			echo
			#for FULL_PLATFORM in $PLATFORMS; do
			#	(
			#	if [ ! -d "$FULL_PLATFORM/$FIRMWARE" ]; then
			#		echo "No $FIRMWARE directory for $FULL_PLATFORM, skipping."
			#		continue
			#	fi
			#	echo
			#	echo "Updating unstable link (Try $i)"
			#	echo "---------------------------------------------"
			#	cd $FULL_PLATFORM/firmware
			#	LATEST="$(ls ../../archive/master/ | sort -V | tail -n 1)"
			#	echo "Latest firmware is $LATEST (current is $(readlink unstable))"
			#	HDMI2USB_FIRMWARE="../../archive/master/$LATEST/$FULL_PLATFORM/hdmi2usb/lm32"
			#	echo "Checking for '$HDMI2USB_FIRMWARE'"
			#	if [ -d "$HDMI2USB_FIRMWARE" -a "$(readlink unstable)" != "$HDMI2USB_FIRMWARE" ]; then
			#		echo "Changing $FULL_PLATFORM from '$(readlink unstable)' to '$HDMI2USB_FIRMWARE'"
			#		ln -sfT "$HDMI2USB_FIRMWARE" unstable
			#		git add unstable
			#		git commit -a \
			#			-m "Updating unstable link (Travis build #$TRAVIS_BUILD_NUMBER of $GIT_REVISION for PLATFORM=$FULL_PLATFORM TARGET=$TARGET CPU=$FULL_CPU FIRMWARE=$FIRMWARE)" \
			#			-m "" \
			#			-m "From https://github.com/$TRAVIS_REPO_SLUG/tree/$TRAVIS_COMMIT" \
			#			-m "$TRAVIS_COMMIT_MESSAGE"
			#	else
			#		echo "Not updating $FULL_PLATFORM"
			#	fi
			#	)
			#done
		else
			echo "Not updating link as on branch '$TRAVIS_BRANCH'"
		fi
		echo
		echo "Merging (Try $i)"
		echo "---------------------------------------------"
		svn update
		echo
		echo "Changes to be pushed (Try $i)"
		echo "---------------------------------------------"
		svn status
		if [ $(svn status | wc -l) -eq 0 ]; then
			break
		fi
		echo
		echo "Pushing (Try $i)"
		echo "---------------------------------------------"
		svn commit 
		if git push --quiet origin master > /dev/null 2>&1 ; then
			echo "Push success!"
		else
			echo "Push failed :-("
		fi
	done
	echo
	echo "Push finished!"
	)
fi
